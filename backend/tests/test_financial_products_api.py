import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_financial_products_api_end_to_end_and_idempotency(client: AsyncClient):
    # --------------------------------------------------------------------------
    # 1. Ingestion Endpoint Execution (First Pass)
    # --------------------------------------------------------------------------
    ingest_res1 = await client.post(f"{settings.API_V1_STR}/financial-products/ingest")
    assert ingest_res1.status_code == 200
    summary1 = ingest_res1.json()
    assert summary1["status"] == "success"
    assert summary1["products_processed"] >= 10
    assert summary1["products_created"] >= 10
    assert summary1["market_records_processed"] >= 20

    total_products = summary1["products_processed"]

    # --------------------------------------------------------------------------
    # 2. Ingestion Idempotency Verification (Second Pass)
    # --------------------------------------------------------------------------
    ingest_res2 = await client.post(f"{settings.API_V1_STR}/financial-products/ingest")
    assert ingest_res2.status_code == 200
    summary2 = ingest_res2.json()
    assert summary2["status"] == "success"
    # Second run should update existing records, creating 0 new products
    assert summary2["products_created"] == 0
    assert summary2["products_updated"] == total_products

    # --------------------------------------------------------------------------
    # 3. List Financial Products
    # --------------------------------------------------------------------------
    list_res = await client.get(f"{settings.API_V1_STR}/financial-products")
    assert list_res.status_code == 200
    products = list_res.json()
    assert len(products) == total_products

    # Grab first product
    first_product = products[0]
    p_id = first_product["id"]
    symbol = first_product["symbol"]
    assert "name" in first_product
    assert "product_type" in first_product
    assert "asset_class" in first_product
    assert "risk_level" in first_product
    assert first_product["currency"] == "INR"

    # --------------------------------------------------------------------------
    # 4. Get Product By ID
    # --------------------------------------------------------------------------
    get_res = await client.get(f"{settings.API_V1_STR}/financial-products/{p_id}")
    assert get_res.status_code == 200
    fetched_prod = get_res.json()
    assert fetched_prod["id"] == p_id
    assert fetched_prod["symbol"] == symbol

    # --------------------------------------------------------------------------
    # 5. Filter Products by Asset Class
    # --------------------------------------------------------------------------
    filter_res = await client.get(
        f"{settings.API_V1_STR}/financial-products/filter",
        params={"asset_class": "equity"},
    )
    assert filter_res.status_code == 200
    equity_prods = filter_res.json()
    assert len(equity_prods) > 0
    assert all(p["asset_class"] == "equity" for p in equity_prods)

    # --------------------------------------------------------------------------
    # 6. Retrieve Market Data for Product
    # --------------------------------------------------------------------------
    # Find NIFTY50-INDX product ID
    nifty_prod = next(p for p in products if p["symbol"] == "NIFTY50-INDX")
    md_res = await client.get(
        f"{settings.API_V1_STR}/financial-products/{nifty_prod['id']}/market-data"
    )
    assert md_res.status_code == 200
    md_series = md_res.json()
    assert len(md_series) >= 5
    assert float(md_series[0]["close_price"]) > 0
    assert "open_price" in md_series[0]
    assert "high_price" in md_series[0]
    assert "low_price" in md_series[0]
    assert md_series[0]["volume"] > 0


@pytest.mark.asyncio
async def test_get_nonexistent_product_returns_404(client: AsyncClient):
    res = await client.get(f"{settings.API_V1_STR}/financial-products/99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_market_data_nonexistent_product_returns_404(client: AsyncClient):
    res = await client.get(f"{settings.API_V1_STR}/financial-products/99999/market-data")
    assert res.status_code == 404
