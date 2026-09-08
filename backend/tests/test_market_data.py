import pytest
from httpx import AsyncClient
from app.market_data.service import get_market_data_service
from app.market_data.schemas import BENCHMARK_INSTRUMENTS



@pytest.mark.asyncio
async def test_get_market_status(client: AsyncClient):
    response = await client.get("/api/v1/market/status")
    assert response.status_code == 200
    data = response.json()
    assert data["exchange"] == "NSE"
    assert "status" in data
    assert "is_trading" in data
    assert isinstance(data["is_trading"], bool)
    assert "message" in data


@pytest.mark.asyncio
async def test_get_benchmark_indices(client: AsyncClient):
    response = await client.get("/api/v1/market/indices")
    assert response.status_code == 200
    data = response.json()
    assert "quotes" in data
    assert "market_status" in data
    assert "source" in data
    
    quotes = data["quotes"]
    assert len(quotes) > 0
    # Should include Nifty 50
    nifty_key = BENCHMARK_INSTRUMENTS["NIFTY_50"]
    assert nifty_key in quotes
    nifty_quote = quotes[nifty_key]
    assert nifty_quote["symbol"] == "NIFTY 50"
    assert float(nifty_quote["ltp"]) > 0


@pytest.mark.asyncio
async def test_get_market_quotes_query_params(client: AsyncClient):
    nifty_key = BENCHMARK_INSTRUMENTS["NIFTY_50"]
    bank_key = BENCHMARK_INSTRUMENTS["NIFTY_BANK"]
    
    response = await client.get(f"/api/v1/market/quotes?instruments={nifty_key}&instruments={bank_key}")
    assert response.status_code == 200
    data = response.json()
    assert nifty_key in data["quotes"]
    assert bank_key in data["quotes"]


@pytest.mark.asyncio
async def test_get_single_quote(client: AsyncClient):
    nifty_key = BENCHMARK_INSTRUMENTS["NIFTY_50"]
    response = await client.get(f"/api/v1/market/quote/{nifty_key}")
    assert response.status_code == 200
    quote = response.json()
    assert quote["instrument_key"] == nifty_key
    assert quote["symbol"] == "NIFTY 50"
    assert float(quote["ltp"]) > 0
    assert float(quote["previous_close"]) > 0


@pytest.mark.asyncio
async def test_market_service_caching():
    # Calling get_quotes twice rapidly should use in-memory cache
    service = get_market_data_service()
    nifty_key = BENCHMARK_INSTRUMENTS["NIFTY_50"]
    quotes1 = await service.get_quotes([nifty_key])
    quotes2 = await service.get_quotes([nifty_key])
    
    assert nifty_key in quotes1.quotes
    assert nifty_key in quotes2.quotes
    assert quotes1.quotes[nifty_key].ltp == quotes2.quotes[nifty_key].ltp

