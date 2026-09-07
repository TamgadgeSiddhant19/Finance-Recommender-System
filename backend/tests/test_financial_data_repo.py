from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.repository import FinancialProductRepository
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductCreate,
    MarketDataCreate,
    ProductRiskLevel,
    ProductType,
)


@pytest.mark.asyncio
async def test_repo_create_and_get_product(db_session: AsyncSession):
    repo = FinancialProductRepository(db_session)
    prod_in = FinancialProductCreate(
        symbol="NIFTY-TEST",
        name="Test Nifty Index Fund",
        product_type=ProductType.index_fund,
        asset_class=AssetClass.equity,
        issuer="Test AMC",
        risk_level=ProductRiskLevel.high,
        expense_ratio=Decimal("0.0020"),
        minimum_investment=Decimal("500.00"),
    )
    product = await repo.create_product(prod_in)
    assert product.id is not None
    assert product.symbol == "NIFTY-TEST"

    # Get by ID
    fetched_by_id = await repo.get_by_id(product.id)
    assert fetched_by_id is not None
    assert fetched_by_id.name == "Test Nifty Index Fund"

    # Get by Symbol
    fetched_by_symbol = await repo.get_by_symbol("nifty-test")
    assert fetched_by_symbol is not None
    assert fetched_by_symbol.id == product.id


@pytest.mark.asyncio
async def test_repo_upsert_product_duplicate_handling(db_session: AsyncSession):
    repo = FinancialProductRepository(db_session)
    prod_in = FinancialProductCreate(
        symbol="DUPLICATE-CHECK",
        name="Original Name",
        product_type=ProductType.stock,
        asset_class=AssetClass.equity,
        issuer="Corp A",
        risk_level=ProductRiskLevel.very_high,
    )
    # First insert
    p1, created1 = await repo.upsert_product(prod_in)
    assert created1 is True
    assert p1.name == "Original Name"

    # Second upsert with updated name & expense ratio
    prod_updated = FinancialProductCreate(
        symbol="DUPLICATE-CHECK",
        name="Updated Name",
        product_type=ProductType.stock,
        asset_class=AssetClass.equity,
        issuer="Corp A",
        risk_level=ProductRiskLevel.very_high,
        expense_ratio=Decimal("0.0010"),
    )
    p2, created2 = await repo.upsert_product(prod_updated)
    assert created2 is False
    assert p2.id == p1.id
    assert p2.name == "Updated Name"
    assert p2.expense_ratio == Decimal("0.0010")


@pytest.mark.asyncio
async def test_repo_filter_products(db_session: AsyncSession):
    repo = FinancialProductRepository(db_session)

    # Insert 3 diverse products
    await repo.create_product(
        FinancialProductCreate(
            symbol="EQ-1",
            name="Equity Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="AMC 1",
            risk_level=ProductRiskLevel.high,
        )
    )
    await repo.create_product(
        FinancialProductCreate(
            symbol="DEBT-1",
            name="Debt Fund",
            product_type=ProductType.bond,
            asset_class=AssetClass.debt,
            issuer="Govt",
            risk_level=ProductRiskLevel.low,
        )
    )
    await repo.create_product(
        FinancialProductCreate(
            symbol="GOLD-1",
            name="Gold ETF",
            product_type=ProductType.etf,
            asset_class=AssetClass.gold,
            issuer="AMC 2",
            risk_level=ProductRiskLevel.moderate,
        )
    )

    # Filter by Asset Class
    equity_list = await repo.filter_products(asset_class=AssetClass.equity)
    assert len(equity_list) == 1
    assert equity_list[0].symbol == "EQ-1"

    # Filter by Risk Level
    low_risk_list = await repo.filter_products(risk_level=ProductRiskLevel.low)
    assert len(low_risk_list) == 1
    assert low_risk_list[0].symbol == "DEBT-1"


@pytest.mark.asyncio
async def test_repo_market_data_insertion_and_date_filtering(db_session: AsyncSession):
    repo = FinancialProductRepository(db_session)
    product = await repo.create_product(
        FinancialProductCreate(
            symbol="MD-TEST",
            name="Market Data Test Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="AMC",
            risk_level=ProductRiskLevel.high,
        )
    )

    base_time = datetime(2026, 8, 1, 9, 15, 0, tzinfo=timezone.utc)

    # Insert 3 chronological price points
    t1 = base_time
    t2 = base_time + timedelta(days=1)
    t3 = base_time + timedelta(days=2)

    await repo.upsert_market_data(
        MarketDataCreate(
            timestamp=t1,
            open_price=Decimal("100.00"),
            high_price=Decimal("105.00"),
            low_price=Decimal("99.00"),
            close_price=Decimal("104.00"),
            volume=50000,
        ),
        product.id,
    )
    await repo.upsert_market_data(
        MarketDataCreate(
            timestamp=t2,
            open_price=Decimal("104.00"),
            high_price=Decimal("108.00"),
            low_price=Decimal("103.50"),
            close_price=Decimal("107.00"),
            volume=60000,
        ),
        product.id,
    )
    await repo.upsert_market_data(
        MarketDataCreate(
            timestamp=t3,
            open_price=Decimal("107.00"),
            high_price=Decimal("110.00"),
            low_price=Decimal("106.00"),
            close_price=Decimal("109.50"),
            volume=55000,
        ),
        product.id,
    )

    # Retrieve all
    all_data = await repo.get_market_data_for_product(product.id)
    assert len(all_data) == 3
    # Compare timestamps agnostic to timezone attachment in SQLite test runs
    assert all_data[0].timestamp.replace(tzinfo=timezone.utc) == t1
    assert all_data[2].timestamp.replace(tzinfo=timezone.utc) == t3

    # Date range filter: Between t1 + 12h and t3 - 12h (should match only t2)
    filtered = await repo.get_market_data_for_product(
        product_id=product.id,
        start_time=t1 + timedelta(hours=12),
        end_time=t3 - timedelta(hours=12),
    )
    assert len(filtered) == 1
    assert filtered[0].timestamp.replace(tzinfo=timezone.utc) == t2
