"""
Unit and Integration Tests for Phase 6.5 Provider-Independent Market Data Foundation.
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.market.adapters.base import MarketDataAdapter
from app.market.adapters.demo import DemoMarketDataAdapter, is_indian_market_hours
from app.market.adapters.upstox import UpstoxMarketDataAdapter
from app.market.exceptions import (
    InstrumentNotFoundError,
    MarketDataError,
    ProviderUnavailableError,
)
from app.market.instrument_mapping import InstrumentMapper, default_instrument_mapper
from app.market.intelligence.analytics import (
    calculate_52_week_range,
    calculate_drawdown,
    calculate_moving_average,
    calculate_returns,
    calculate_rsi,
    calculate_volatility,
    calculate_volume_change,
)
from app.market.schemas import HistoricalCandle, InstrumentInfo, MarketQuote
from app.market.service import MarketDataService, get_market_data_service


# ---------------------------------------------------------------------------
# 1. Market Data Adapter & Demo Provider Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_demo_adapter_quote_provenance():
    """Verify demo adapter explicitly sets data_source='demo' and data_status='synthetic'."""
    adapter = DemoMarketDataAdapter()
    assert adapter.name == "demo"
    assert adapter.is_configured is True

    quote = await adapter.get_quote("TCS")
    assert quote is not None
    assert quote.symbol == "TCS"
    assert quote.data_source == "demo"
    assert quote.data_status == "synthetic"
    assert quote.price > Decimal("0.00")
    assert quote.previous_close > Decimal("0.00")
    assert quote.ohlc is not None


@pytest.mark.asyncio
async def test_demo_adapter_historical_candles():
    """Verify demo adapter returns well-formed synthetic historical candle series."""
    adapter = DemoMarketDataAdapter()
    candles = await adapter.get_historical_data("NIFTY 50", interval="day")

    assert len(candles) > 0
    first_candle = candles[0]
    assert first_candle.data_source == "demo"
    assert first_candle.data_status == "synthetic"
    assert first_candle.open > Decimal("0.00")
    assert first_candle.high >= first_candle.low


@pytest.mark.asyncio
async def test_demo_adapter_market_status():
    """Verify market status includes IST trading session calculation and provenance."""
    adapter = DemoMarketDataAdapter()
    status = await adapter.get_market_status("NSE")

    assert status.exchange == "NSE"
    assert status.status in ["OPEN", "CLOSED"]
    assert isinstance(status.is_trading, bool)
    assert status.data_source == "demo"
    assert status.data_status == "synthetic"


@pytest.mark.asyncio
async def test_upstox_adapter_unconfigured_safety():
    """Verify Upstox adapter gracefully returns unconfigured status when token is missing."""
    adapter = UpstoxMarketDataAdapter(access_token=None)
    assert adapter.name == "upstox"
    assert adapter.is_configured is False

    quote = await adapter.get_quote("TCS")
    assert quote is not None
    assert quote.data_source == "upstox"
    assert quote.data_status == "unconfigured"
    assert quote.price == Decimal("0.00")

    status = await adapter.get_market_status("NSE")
    assert status.data_source == "upstox"
    assert status.data_status == "unconfigured"


# ---------------------------------------------------------------------------
# 2. Instrument Mapping Layer Tests
# ---------------------------------------------------------------------------

def test_instrument_mapper_normalization():
    """Verify symbol normalization and reverse key resolution."""
    mapper = InstrumentMapper()

    assert mapper.normalize_symbol("tcs") == "TCS"
    assert mapper.normalize_symbol("nifty_50") == "NIFTY 50"
    assert mapper.normalize_symbol("NSE_EQ|INE467B01029") == "TCS"
    assert mapper.normalize_symbol("NSE_INDEX:Nifty 50") == "NIFTY 50"

    # Provider key synthesis
    assert mapper.get_provider_key("TCS") == "NSE_EQ|INE467B01029"
    assert mapper.get_provider_key("NIFTY 50") == "NSE_INDEX|Nifty 50"
    assert mapper.get_provider_key("UNKNOWN_SYM") == "NSE_EQ|UNKNOWN_SYM"


def test_instrument_mapper_registration():
    """Verify custom instrument registration."""
    mapper = InstrumentMapper()
    custom_info = InstrumentInfo(
        symbol="ZOMATO",
        name="Zomato Ltd",
        exchange="NSE",
        instrument_type="EQUITY",
        provider_key="NSE_EQ|INE758T01015",
        is_active=True,
        data_source="custom_test",
    )
    mapper.register_instrument(custom_info)

    assert mapper.normalize_symbol("zomato") == "ZOMATO"
    assert mapper.normalize_symbol("NSE_EQ|INE758T01015") == "ZOMATO"
    assert mapper.get_instrument_info("ZOMATO") is not None


# ---------------------------------------------------------------------------
# 3. Market Data Service Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_market_service_caching_and_batch():
    """Verify caching, TTL behavior, and batch quote retrieval."""
    adapter = DemoMarketDataAdapter()
    service = MarketDataService(adapter=adapter, cache_ttl_seconds=10)

    # Initial fetch
    batch = await service.get_quotes(["TCS", "INFY"])
    assert "TCS" in batch.quotes
    assert "INFY" in batch.quotes
    assert batch.data_source == "demo"
    assert batch.data_status == "synthetic"

    # Second fetch should hit cache
    cached_batch = await service.get_quotes(["TCS"])
    assert cached_batch.quotes["TCS"].price == batch.quotes["TCS"].price


@pytest.mark.asyncio
async def test_market_service_benchmark_indices():
    """Verify service retrieves benchmark indices."""
    service = get_market_data_service()
    benchmarks = await service.get_benchmark_indices()

    assert "NIFTY 50" in benchmarks.quotes
    assert "NIFTY BANK" in benchmarks.quotes
    assert "INDIA VIX" in benchmarks.quotes


# ---------------------------------------------------------------------------
# 4. Market Intelligence Analytics Tests
# ---------------------------------------------------------------------------

def test_intelligence_calculate_returns():
    prices = [Decimal("100.00"), Decimal("105.00"), Decimal("110.00"), Decimal("120.00")]
    ret = calculate_returns(prices)
    assert ret == Decimal("20.0000")

    # Single or empty price sequence
    assert calculate_returns([]) == Decimal("0.00")
    assert calculate_returns([Decimal("100.00")]) == Decimal("0.00")


def test_intelligence_calculate_volatility():
    prices = [
        Decimal("100.00"),
        Decimal("102.00"),
        Decimal("99.00"),
        Decimal("101.00"),
        Decimal("103.00"),
        Decimal("100.00"),
    ]
    vol = calculate_volatility(prices, annualize=True)
    assert vol > Decimal("0.00")
    assert isinstance(vol, Decimal)


def test_intelligence_calculate_moving_average():
    prices = [Decimal("10.00"), Decimal("20.00"), Decimal("30.00"), Decimal("40.00")]
    sma2 = calculate_moving_average(prices, window=2)
    assert len(sma2) == 4
    assert sma2[0] == Decimal("10.00")  # Expanding first element
    assert sma2[1] == Decimal("15.00")  # (10+20)/2
    assert sma2[2] == Decimal("25.00")  # (20+30)/2
    assert sma2[3] == Decimal("35.00")  # (30+40)/2


def test_intelligence_calculate_rsi():
    # Uptrend prices -> RSI should be high (> 50)
    uptrend = [Decimal(f"{100 + i * 2}") for i in range(20)]
    rsi_up = calculate_rsi(uptrend, period=14)
    assert rsi_up > Decimal("50.00")

    # Downtrend prices -> RSI should be low (< 50)
    downtrend = [Decimal(f"{200 - i * 2}") for i in range(20)]
    rsi_down = calculate_rsi(downtrend, period=14)
    assert rsi_down < Decimal("50.00")


def test_intelligence_calculate_drawdown():
    prices = [
        Decimal("100.00"),
        Decimal("150.00"),  # Peak
        Decimal("120.00"),  # Drop of 20% from peak
        Decimal("105.00"),  # Drop of 30% from peak (Max Drawdown = -30%)
        Decimal("135.00"),  # Current price (Current Drawdown = -10%)
    ]
    max_dd, curr_dd = calculate_drawdown(prices)
    assert max_dd == Decimal("-30.00")
    assert curr_dd == Decimal("-10.00")


def test_intelligence_calculate_52_week_range():
    now = datetime.now(timezone.utc)
    candles = [
        HistoricalCandle(
            timestamp=now,
            open=Decimal("100.00"),
            high=Decimal("125.00"),
            low=Decimal("95.00"),
            close=Decimal("110.00"),
            volume=1000,
            data_source="demo",
            data_status="synthetic",
        ),
        HistoricalCandle(
            timestamp=now,
            open=Decimal("110.00"),
            high=Decimal("145.00"),
            low=Decimal("105.00"),
            close=Decimal("140.00"),
            volume=2000,
            data_source="demo",
            data_status="synthetic",
        ),
    ]
    low_52, high_52 = calculate_52_week_range(candles)
    assert low_52 == Decimal("95.00")
    assert high_52 == Decimal("145.00")


def test_intelligence_calculate_volume_change():
    now = datetime.now(timezone.utc)
    candles = [
        HistoricalCandle(
            timestamp=now,
            open=Decimal("100.00"),
            high=Decimal("105.00"),
            low=Decimal("95.00"),
            close=Decimal("102.00"),
            volume=1000,
            data_source="demo",
            data_status="synthetic",
        )
        for _ in range(5)
    ]
    # Add high-volume candle
    candles.append(
        HistoricalCandle(
            timestamp=now,
            open=Decimal("102.00"),
            high=Decimal("108.00"),
            low=Decimal("101.00"),
            close=Decimal("107.00"),
            volume=2000,  # 100% higher than 1000 average
            data_source="demo",
            data_status="synthetic",
        )
    )
    vol_change = calculate_volume_change(candles, window=5)
    assert vol_change == Decimal("100.00")


# ---------------------------------------------------------------------------
# 5. REST API Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_market_status(client: AsyncClient):
    """GET /api/v1/market/status"""
    response = await client.get("/api/v1/market/status")
    assert response.status_code == 200
    data = response.json()
    assert data["exchange"] == "NSE"
    assert "status" in data
    assert "is_trading" in data
    assert data["data_source"] == "demo"
    assert data["data_status"] == "synthetic"


@pytest.mark.asyncio
async def test_api_market_instruments(client: AsyncClient):
    """GET /api/v1/market/instruments"""
    response = await client.get("/api/v1/market/instruments")
    assert response.status_code == 200
    instruments = response.json()
    assert isinstance(instruments, list)
    assert len(instruments) > 0
    symbols = [i["symbol"] for i in instruments]
    assert "TCS" in symbols
    assert "NIFTY 50" in symbols


@pytest.mark.asyncio
async def test_api_market_quote_single(client: AsyncClient):
    """GET /api/v1/market/quote/{symbol}"""
    response = await client.get("/api/v1/market/quote/TCS")
    assert response.status_code == 200
    quote = response.json()
    assert quote["symbol"] == "TCS"
    assert float(quote["price"]) > 0
    assert float(quote["previous_close"]) > 0
    assert quote["data_source"] == "demo"
    assert quote["data_status"] == "synthetic"


@pytest.mark.asyncio
async def test_api_market_history_single(client: AsyncClient):
    """GET /api/v1/market/history/{symbol}"""
    response = await client.get("/api/v1/market/history/TCS?interval=day")
    assert response.status_code == 200
    candles = response.json()
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert candles[0]["data_source"] == "demo"
    assert candles[0]["data_status"] == "synthetic"


@pytest.mark.asyncio
async def test_api_market_indices(client: AsyncClient):
    """GET /api/v1/market/indices"""
    response = await client.get("/api/v1/market/indices")
    assert response.status_code == 200
    data = response.json()
    assert "quotes" in data
    assert "NIFTY 50" in data["quotes"]
    assert data["data_source"] == "demo"
    assert data["data_status"] == "synthetic"


@pytest.mark.asyncio
async def test_api_market_batch_quotes(client: AsyncClient):
    """GET /api/v1/market/quotes?instruments=TCS,INFY"""
    response = await client.get("/api/v1/market/quotes?instruments=TCS,INFY")
    assert response.status_code == 200
    data = response.json()
    assert "TCS" in data["quotes"]
    assert "INFY" in data["quotes"]
