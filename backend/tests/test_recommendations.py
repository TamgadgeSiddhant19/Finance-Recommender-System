from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import make_auth_headers


from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductResponse,
    ProductRiskLevel,
    ProductType,
)
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.recommendations.allocation import generate_target_allocation
from app.recommendations.constants import ALLOWED_PRODUCT_RISK_MAP
from app.recommendations.filters import filter_eligible_products
from app.recommendations.portfolio import construct_portfolio
from app.recommendations.schemas import (
    RecommendedPortfolioItem,
    TargetAllocationSummary,
)
from app.recommendations.scoring import score_product
from app.recommendations.service import RecommendationService
from app.recommendations.validators import validate_portfolio
from app.schemas.enums import (
    GoalType,
    InvestmentExperience,
    Priority,
    RiskTolerance,
)

from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase


def get_mock_products():
    return [
        FinancialProduct(
            id=1,
            symbol="NIFTY50-INDX",
            name="Nifty 50 Index Fund",
            product_type=ProductType.index_fund,
            asset_class=AssetClass.equity,
            issuer="UTI Mutual Fund",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.high,
            expense_ratio=Decimal("0.0020"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=2,
            symbol="FLEXICAP-EQ",
            name="Parag Parikh Flexi Cap Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="PPFAS Mutual Fund",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.high,
            expense_ratio=Decimal("0.0065"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=3,
            symbol="CORPBOND-DBT",
            name="ICICI Prudential Corporate Bond Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.debt,
            issuer="ICICI Prudential AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.moderate,
            expense_ratio=Decimal("0.0035"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=4,
            symbol="PPF-GOV",
            name="Public Provident Fund Scheme",
            product_type=ProductType.government_security,
            asset_class=AssetClass.debt,
            issuer="Government of India",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.low,
            expense_ratio=Decimal("0.0000"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=5,
            symbol="GOLDetf-COMM",
            name="Nippon India ETF Gold BeES",
            product_type=ProductType.etf,
            asset_class=AssetClass.gold,
            issuer="Nippon Life India AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.moderate,
            expense_ratio=Decimal("0.0050"),
            minimum_investment=Decimal("100.00"),
        ),
        FinancialProduct(
            id=6,
            symbol="LIQUID-CSH",
            name="Mirae Asset Cash Management Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.cash,
            issuer="Mirae Asset AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.low,
            expense_ratio=Decimal("0.0015"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=7,
            symbol="MIDCAP-EQ",
            name="HDFC Mid-Cap Opportunities Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="HDFC AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.very_high,
            expense_ratio=Decimal("0.0075"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=8,
            symbol="BANKFD-1Y",
            name="HDFC Bank 1-Year Fixed Deposit",
            product_type=ProductType.fixed_deposit,
            asset_class=AssetClass.debt,
            issuer="HDFC Bank",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.low,
            expense_ratio=Decimal("0.0000"),
            minimum_investment=Decimal("5000.00"),
        ),
    ]


# ------------------------------------------------------------------------------
# 1. Unit Tests for Filters & Scoring
# ------------------------------------------------------------------------------

def test_product_risk_filtering_conservative():
    products = get_mock_products()
    eligible, exclusions = filter_eligible_products(
        products=products,
        risk_category="CONSERVATIVE",
        investment_capacity=Decimal("20000.00"),
    )
    # Conservative allows low and moderate only
    for p in eligible:
        assert p.risk_level in [ProductRiskLevel.low, ProductRiskLevel.moderate]
    assert any(ex["symbol"] == "NIFTY50-INDX" for ex in exclusions)
    assert any(ex["symbol"] == "MIDCAP-EQ" for ex in exclusions)


def test_product_risk_filtering_moderate_and_aggressive():
    products = get_mock_products()
    eligible_mod, _ = filter_eligible_products(
        products=products,
        risk_category="MODERATE",
        investment_capacity=Decimal("20000.00"),
    )
    # Moderate includes high (Nifty50) but excludes very_high (MIDCAP-EQ)
    mod_symbols = [p.symbol for p in eligible_mod]
    assert "NIFTY50-INDX" in mod_symbols
    assert "MIDCAP-EQ" not in mod_symbols

    eligible_agg, _ = filter_eligible_products(
        products=products,
        risk_category="AGGRESSIVE",
        investment_capacity=Decimal("20000.00"),
    )
    agg_symbols = [p.symbol for p in eligible_agg]
    assert "MIDCAP-EQ" in agg_symbols


def test_minimum_investment_filtering():
    products = get_mock_products()
    # If user capacity is only 2000, 5000 min investment FD should be filtered out
    eligible, exclusions = filter_eligible_products(
        products=products,
        risk_category="CONSERVATIVE",
        investment_capacity=Decimal("2000.00"),
    )
    eligible_symbols = [p.symbol for p in eligible]
    assert "BANKFD-1Y" not in eligible_symbols
    assert any(ex["symbol"] == "BANKFD-1Y" for ex in exclusions)


def test_deterministic_scoring_repeatability():
    product = get_mock_products()[0]  # Nifty 50 Index Fund
    target_dict = {"equity": Decimal("55.00"), "debt": Decimal("35.00"), "gold": Decimal("10.00"), "cash": Decimal("0.00")}

    score1, reasons1 = score_product(
        product=product,
        user_risk_cat="MODERATE",
        monthly_capacity=Decimal("25000.00"),
        target_allocation_dict=target_dict,
        goals=[],
    )
    score2, reasons2 = score_product(
        product=product,
        user_risk_cat="MODERATE",
        monthly_capacity=Decimal("25000.00"),
        target_allocation_dict=target_dict,
        goals=[],
    )

    assert score1 == score2
    assert Decimal("0.00") <= score1 <= Decimal("100.00")
    assert len(reasons1) == 5
    assert len(reasons2) == 5


# ------------------------------------------------------------------------------
# 2. Asset Allocation & Portfolio Construction Tests
# ------------------------------------------------------------------------------

def test_asset_allocation_sums_to_100():
    for cat in ["CONSERVATIVE", "MODERATE", "AGGRESSIVE", "VERY_AGGRESSIVE"]:
        alloc = generate_target_allocation(risk_category=cat)
        total = alloc.equity_pct + alloc.debt_pct + alloc.gold_pct + alloc.cash_pct
        assert total == Decimal("100.00")


def test_asset_allocation_tactical_horizon_shift():
    # Short-term goal (< 3 years) should cap equity at 25% max even for aggressive profiles
    short_goal = FinancialGoalBase(
        goal_type=GoalType.emergency_fund,
        target_amount=Decimal("200000.00"),
        target_years=2,
        priority=Priority.high,
    )
    alloc = generate_target_allocation(risk_category="AGGRESSIVE", goals=[short_goal])
    total = alloc.equity_pct + alloc.debt_pct + alloc.gold_pct + alloc.cash_pct
    assert total == Decimal("100.00")
    assert alloc.equity_pct <= Decimal("25.00")
    assert alloc.debt_pct >= Decimal("50.00")



def test_portfolio_construction_and_validation():
    products = get_mock_products()
    profile = FinancialProfileBase(
        age=30,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("300000.00"),
        monthly_investment_capacity=Decimal("25000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )

    rec = RecommendationService.generate_recommendation(
        profile=profile,
        goals=[],
        available_products=products,
    )

    assert rec.risk_category == "MODERATE"
    assert rec.total_monthly_sip <= Decimal("25000.00")
    assert rec.validation_report.is_valid is True

    total_alloc_pct = sum(item.allocation_percentage for item in rec.portfolio_items)
    assert abs(total_alloc_pct - Decimal("100.00")) <= Decimal("0.50")


def test_portfolio_validation_failure_cases():
    target_alloc = TargetAllocationSummary(
        equity_pct=Decimal("50.00"),
        debt_pct=Decimal("30.00"),
        gold_pct=Decimal("10.00"),
        cash_pct=Decimal("10.00"),
    )

    # 1. Empty portfolio
    val_empty = validate_portfolio(
        portfolio_items=[],
        target_allocation=target_alloc,
        monthly_capacity=Decimal("20000.00"),
        risk_category="MODERATE",
        eligible_product_ids=set(),
    )
    assert val_empty.is_valid is False
    assert len(val_empty.error_messages) > 0

    # 2. Total allocation != 100%
    bad_item = RecommendedPortfolioItem(
        product_id=1,
        symbol="NIFTY50-INDX",
        name="Nifty 50 Index Fund",
        product_type=ProductType.index_fund,
        asset_class=AssetClass.equity,
        risk_level=ProductRiskLevel.high,
        suitability_score=Decimal("80.00"),
        allocation_percentage=Decimal("40.00"),  # Only 40%, missing 60%
        suggested_monthly_sip=Decimal("8000.00"),
        suggested_lump_sum=Decimal("0.00"),
        selection_reasons=[],
    )
    val_bad = validate_portfolio(
        portfolio_items=[bad_item],
        target_allocation=target_alloc,
        monthly_capacity=Decimal("20000.00"),
        risk_category="MODERATE",
        eligible_product_ids={1},
    )
    assert val_bad.is_valid is False
    assert any("violating 100.00%" in err for err in val_bad.error_messages)


# ------------------------------------------------------------------------------
# 3. Integration & API Endpoint Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommendation_api_simulate(client: AsyncClient, db_session: AsyncSession):
    # Seed products
    for p in get_mock_products():
        db_session.add(p)
    await db_session.commit()

    payload = {
        "profile": {
            "age": 28,
            "monthly_income": 120000.0,
            "monthly_expenses": 60000.0,
            "total_savings": 250000.0,
            "monthly_investment_capacity": 30000.0,
            "total_debt": 0.0,
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
        },
        "goals": [
            {
                "goal_type": "wealth_creation",
                "target_amount": 5000000.0,
                "current_amount": 0.0,
                "target_years": 10,
                "priority": "high",
            }
        ],
    }

    response = await client.post("/api/v1/recommendations/simulate", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"

    data = response.json()
    assert data["risk_category"] == "MODERATE"
    assert len(data["portfolio_items"]) > 0
    assert data["validation_report"]["is_valid"] is True
    assert float(data["total_monthly_sip"]) <= 30000.0



@pytest.mark.asyncio
async def test_recommendation_api_user_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Seed products
    for p in get_mock_products():
        db_session.add(p)

    # 2. Seed User
    user = User(email="rec_test@example.com", password_hash="dummy_hash")
    db_session.add(user)
    await db_session.flush()

    # 3. Seed Profile
    profile = FinancialProfile(
        user_id=user.id,
        age=35,
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("70000.00"),
        total_savings=Decimal("500000.00"),
        monthly_investment_capacity=Decimal("40000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.aggressive,
        investment_experience=InvestmentExperience.advanced,
    )
    db_session.add(profile)

    # 4. Seed Goal
    goal = FinancialGoal(
        user_id=user.id,
        goal_type=GoalType.retirement,
        target_amount=Decimal("10000000.00"),
        target_years=15,
        priority=Priority.high,
    )
    db_session.add(goal)
    await db_session.commit()

    # 5. Unauthenticated call must fail with 401
    unauth_res = await client.post(f"/api/v1/recommendations/{user.id}")
    assert unauth_res.status_code == 401

    headers = make_auth_headers(user.id)

    # 6. Generate and Save Recommendation via POST
    post_res = await client.post(f"/api/v1/recommendations/{user.id}", headers=headers)
    assert post_res.status_code == 201
    post_data = post_res.json()
    assert post_data["user_id"] == user.id
    assert post_data["recommendation_id"] is not None
    assert post_data["risk_category"] in ["AGGRESSIVE", "VERY_AGGRESSIVE"]
    rec_id = post_data["recommendation_id"]

    # 7. Retrieve History via GET /recommendations/{user_id}
    history_res = await client.get(f"/api/v1/recommendations/{user.id}", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) >= 1
    assert history_data[0]["id"] == rec_id

    # 8. Retrieve Detail via GET /recommendations/{user_id}/{rec_id}
    detail_res = await client.get(f"/api/v1/recommendations/{user.id}/{rec_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["recommendation_id"] == rec_id
    assert len(detail_data["portfolio_items"]) > 0
    assert detail_data["validation_report"]["is_valid"] is True

    # 9. Verify /recommendations/me
    me_res = await client.get("/api/v1/recommendations/me", headers=headers)
    assert me_res.status_code == 200
    assert len(me_res.json()) >= 1

