import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import AssetClass, ProductRiskLevel, ProductType
from app.market.schemas import HistoricalCandle
from app.market.adapters.alphavantage import AlphaVantageMarketDataAdapter
from app.models.financial_goal import FinancialGoal
from app.recommendations.product_intelligence import (
    ProductIntelligenceReport,
    build_product_intelligence,
    compute_market_intelligence_features,
)
from app.recommendations.scoring import (
    score_product,
    calculate_market_performance_fit,
)
from app.recommendations.filters import filter_eligible_products


def create_sample_product(
    id: int,
    symbol: str,
    name: str,
    asset_class: AssetClass,
    risk_level: ProductRiskLevel,
    expense_ratio: float = 0.5,
    min_investment: float = 500.0,
) -> FinancialProduct:
    return FinancialProduct(
        id=id,
        symbol=symbol,
        name=name,
        product_type=ProductType.mutual_fund,
        asset_class=asset_class,
        issuer="Test Asset Management",
        currency="INR",
        country="India",
        risk_level=risk_level,
        expense_ratio=Decimal(str(expense_ratio)),
        minimum_investment=Decimal(str(min_investment)),
    )


def create_test_candles(start_price: float, end_price: float, days: int = 300) -> list[HistoricalCandle]:
    base_date = date.today() - timedelta(days=days)
    candles = []
    step = (end_price - start_price) / (days - 1) if days > 1 else 0.0
    for i in range(days):
        d = base_date + timedelta(days=i)
        p = Decimal(str(round(start_price + step * i, 4)))
        candles.append(HistoricalCandle(
            timestamp=datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc),
            open=p,
            high=p * Decimal("1.01"),
            low=p * Decimal("0.99"),
            close=p,
            volume=1000,
            data_source="alphavantage",
            data_status="historical",
        ))
    return candles


def test_product_intelligence_report_with_candles():
    product = create_sample_product(1, "NIFTYBEES", "Nifty 50 ETF", AssetClass.equity, ProductRiskLevel.moderate, 0.05, 500)
    candles = create_test_candles(start_price=100.0, end_price=120.0, days=300)

    report = build_product_intelligence(
        product=product,
        user_risk_cat="MODERATE",
        monthly_capacity=Decimal("25000.00"),
        goals=[],
        candles=candles,
    )

    assert report.symbol == "NIFTYBEES"
    assert report.historical_return_1y is not None
    assert report.historical_return_1y > 0  # ~20%
    assert report.volatility is not None
    assert report.max_drawdown is not None
    assert report.data_quality_score >= Decimal("75.00")
    assert report.data_source == "alphavantage"
    assert report.data_status == "historical"


def test_product_intelligence_report_missing_candles():
    product = create_sample_product(2, "PPF", "Public Provident Fund", AssetClass.debt, ProductRiskLevel.low, 0.0, 500)

    report = build_product_intelligence(
        product=product,
        user_risk_cat="CONSERVATIVE",
        monthly_capacity=Decimal("15000.00"),
        goals=[],
        candles=[],
    )

    assert report.historical_return_1y is None
    assert report.volatility is None
    assert report.max_drawdown is None
    assert report.data_quality_score == Decimal("0.00")
    assert report.data_source == "master_catalog"
    assert report.data_status == "unavailable"


def test_anti_return_chasing_market_performance_score():
    # Product with high returns (80%) but excessive volatility (35%) and heavy drawdown (-40%)
    high_risk_report = ProductIntelligenceReport(
        product_id=1,
        symbol="SPECULATIVE",
        name="Speculative Fund",
        asset_class="equity",
        risk_level="very_high",
        expense_ratio=Decimal("2.50"),
        historical_return_1y=Decimal("80.00"),
        volatility=Decimal("35.00"),  # Highly volatile
        max_drawdown=Decimal("-40.00"),  # Severe drawdown
        data_quality_score=Decimal("90.00"),
        risk_compatibility_score=Decimal("30.00"),
        goal_compatibility_score=Decimal("40.00"),
        horizon_compatibility_score=Decimal("50.00"),
        cost_efficiency_score=Decimal("50.00"),
        ticket_sizing_score=Decimal("60.00"),
    )

    score, desc = calculate_market_performance_fit(high_risk_report)
    # Market score should be penalized (-15 for vol, -10 for dd) -> 65
    assert score <= Decimal("65.00")

    # Stable product with moderate returns and low volatility
    stable_report = ProductIntelligenceReport(
        product_id=2,
        symbol="STABLE",
        name="Stable Large Cap",
        asset_class="equity",
        risk_level="moderate",
        expense_ratio=Decimal("0.20"),
        historical_return_1y=Decimal("15.00"),
        volatility=Decimal("12.00"),
        max_drawdown=Decimal("-8.00"),
        data_quality_score=Decimal("90.00"),
        risk_compatibility_score=Decimal("80.00"),
        goal_compatibility_score=Decimal("80.00"),
        horizon_compatibility_score=Decimal("80.00"),
        cost_efficiency_score=Decimal("90.00"),
        ticket_sizing_score=Decimal("80.00"),
    )

    stable_score, _ = calculate_market_performance_fit(stable_report)
    assert stable_score >= Decimal("80.00")
    assert stable_score > score


def test_hard_risk_filter_preempts_high_scores():
    conservative_product = create_sample_product(1, "DEBT_FUND", "Short Term Debt", AssetClass.debt, ProductRiskLevel.low, 0.3, 500)
    aggressive_product = create_sample_product(2, "CRYPTO_FUND", "High Beta Crypto", AssetClass.equity, ProductRiskLevel.very_high, 1.5, 500)

    products = [conservative_product, aggressive_product]

    # For a CONSERVATIVE user, VERY_HIGH risk product must be filtered out immediately
    eligible_products, excluded_summaries = filter_eligible_products(
        products=products,
        risk_category="CONSERVATIVE",
        investment_capacity=Decimal("10000.00"),
    )

    assert len(eligible_products) == 1
    assert eligible_products[0].symbol == "DEBT_FUND"
    assert len(excluded_summaries) == 1
    assert excluded_summaries[0]["symbol"] == "CRYPTO_FUND"
    assert "exceeds allowed risk levels" in excluded_summaries[0]["reason"].lower()


def test_deterministic_reasons_generation():
    product = create_sample_product(1, "NIFTY50", "Nifty 50 Index Fund", AssetClass.equity, ProductRiskLevel.moderate, 0.1, 500)
    report = ProductIntelligenceReport(
        product_id=1,
        symbol="NIFTY50",
        name="Nifty 50 Index Fund",
        asset_class="equity",
        risk_level="moderate",
        expense_ratio=Decimal("0.10"),
        historical_return_1y=Decimal("14.50"),
        volatility=Decimal("13.00"),
        max_drawdown=Decimal("-10.00"),
        data_quality_score=Decimal("95.00"),
        data_source="alphavantage",
        data_status="historical",
        risk_compatibility_score=Decimal("85.00"),
        goal_compatibility_score=Decimal("80.00"),
        horizon_compatibility_score=Decimal("90.00"),
        cost_efficiency_score=Decimal("90.00"),
        ticket_sizing_score=Decimal("80.00"),
    )

    target_allocation_dict = {"equity": Decimal("60.00"), "debt": Decimal("30.00"), "gold": Decimal("10.00"), "cash": Decimal("0.00")}

    suitability_score, reasons, intel = score_product(
        product=product,
        user_risk_cat="MODERATE",
        monthly_capacity=Decimal("20000.00"),
        target_allocation_dict=target_allocation_dict,
        goals=[],
        intelligence_report=report,
    )

    assert suitability_score > Decimal("70.00")
    categories = [r.category for r in reasons]
    assert "Risk Suitability" in categories
    assert "Goal Horizon Fit" in categories
    assert "Cost Efficiency" in categories
    assert "Market Performance Fit" in categories
    assert "Data Quality" in categories


def test_alphavantage_adapter_historical_parsing():
    adapter = AlphaVantageMarketDataAdapter(api_key="test_key")

    mock_raw_json = {
        "Meta Data": {
            "1. Information": "Daily Prices (open, high, low, close) and Volumes",
            "2. Symbol": "IBM",
            "3. Last Refreshed": "2026-03-01",
        },
        "Time Series (Daily)": {
            "2026-03-01": {
                "1. open": "150.00",
                "2. high": "152.00",
                "3. low": "149.50",
                "4. close": "151.50",
                "5. volume": "120000",
            },
            "2026-02-28": {
                "1. open": "148.00",
                "2. high": "150.50",
                "3. low": "147.50",
                "4. close": "149.80",
                "5. volume": "110000",
            }
        }
    }

    candles = adapter._parse_time_series_daily(mock_raw_json)
    assert len(candles) == 2
    assert candles[0].close == Decimal("149.80")
    assert candles[1].close == Decimal("151.50")
