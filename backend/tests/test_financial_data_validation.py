from datetime import datetime, timezone
from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.financial_data.adapters.csv_adapter import CSVAdapter
from app.financial_data.normalizer import quantize_decimal
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductCreate,
    MarketDataBase,
    ProductRiskLevel,
    ProductType,
)
from app.financial_data.validators import (
    validate_market_data,
    validate_product_data,
)


def test_valid_financial_product_schema():
    product = FinancialProductCreate(
        symbol="NIFTY50",
        name="UTI Nifty 50 Index Fund",
        product_type=ProductType.index_fund,
        asset_class=AssetClass.equity,
        issuer="UTI AMC",
        currency="INR",
        country="India",
        risk_level=ProductRiskLevel.high,
        expense_ratio=Decimal("0.0020"),
        minimum_investment=Decimal("500.00"),
    )
    is_valid, errors = validate_product_data(product)
    assert is_valid is True
    assert len(errors) == 0


def test_invalid_product_type_rejected():
    with pytest.raises(ValidationError):
        FinancialProductCreate(
            symbol="INVALID-TYPE",
            name="Invalid Product",
            product_type="cryptocurrency",  # Not in ProductType enum
            asset_class=AssetClass.equity,
            issuer="Test",
            risk_level=ProductRiskLevel.high,
        )


def test_invalid_asset_class_rejected():
    with pytest.raises(ValidationError):
        FinancialProductCreate(
            symbol="INVALID-ASSET",
            name="Invalid Asset Class",
            product_type=ProductType.mutual_fund,
            asset_class="real_estate_speculation",  # Not in AssetClass enum
            issuer="Test",
            risk_level=ProductRiskLevel.high,
        )


def test_invalid_risk_level_rejected():
    with pytest.raises(ValidationError):
        FinancialProductCreate(
            symbol="INVALID-RISK",
            name="Invalid Risk",
            product_type=ProductType.stock,
            asset_class=AssetClass.equity,
            issuer="Test",
            risk_level="extreme_gambling",  # Not in ProductRiskLevel enum
        )


def test_decimal_quantization_and_rounding():
    d1 = quantize_decimal("125.456", 2)
    assert d1 == Decimal("125.46")
    d2 = quantize_decimal(0.00251, 4)
    assert d2 == Decimal("0.0025")
    d3 = quantize_decimal("", 2)
    assert d3 == Decimal("0.00")


def test_negative_price_and_ohlc_invariants_rejected():
    # 1. Negative price rejected by Pydantic schema validation
    with pytest.raises(ValidationError):
        MarketDataBase(
            timestamp=datetime.now(timezone.utc),
            open_price=Decimal("-10.00"),
            high_price=Decimal("15.00"),
            low_price=Decimal("5.00"),
            close_price=Decimal("12.00"),
            volume=1000,
        )

    # 2. High lower than Low rejected by domain validator
    md_broken = MarketDataBase(
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal("100.00"),
        high_price=Decimal("90.00"),  # Broken: High < Low
        low_price=Decimal("95.00"),
        close_price=Decimal("92.00"),
        volume=1000,
    )
    is_valid_b, errors_b = validate_market_data(md_broken)
    assert is_valid_b is False
    assert any("cannot be lower than low" in e.lower() for e in errors_b)


def test_csv_adapter_parsing_and_error_diagnostics():
    adapter = CSVAdapter()

    csv_content = """symbol,name,product_type,asset_class,issuer,currency,country,risk_level,expense_ratio,minimum_investment
VALID1,Valid Mutual Fund,mutual_fund,equity,HDFC AMC,INR,India,high,0.0050,500.00
BAD_ENUM,Invalid Type Fund,bad_type,equity,HDFC AMC,INR,India,high,0.0050,500.00
BAD_MIN,Negative Min Fund,mutual_fund,debt,ICICI AMC,INR,India,low,0.0010,-500.00
"""
    products, errors = adapter.load_products(csv_content)
    assert len(products) == 1
    assert products[0].symbol == "VALID1"
    assert len(errors) == 2
    assert "BAD_ENUM" in errors[0]
    assert "BAD_MIN" in errors[1]


def test_csv_adapter_missing_required_headers():
    adapter = CSVAdapter()
    broken_csv = """symbol,name
TEST1,Incomplete Fields
"""
    products, errors = adapter.load_products(broken_csv)
    assert len(products) == 0
    assert len(errors) > 0
    assert "Missing required fields" in errors[0]
