"""
Isolated Demo / Synthetic Market Data Adapter.
Used for local testing and development when real broker credentials are unconfigured.

CRITICAL INTEGRITY RULES:
- All quotes and candles are explicitly marked with data_source="demo" and data_status="synthetic".
- Demo data is NEVER misrepresented as live, real-time market data.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Dict, List, Optional
from app.market.adapters.base import MarketDataAdapter
from app.market.instrument_mapping import InstrumentMapper, default_instrument_mapper
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketStatusResponse,
    OHLCData,
)


def is_indian_market_hours(dt: Optional[datetime] = None) -> bool:
    """
    Determines if Indian equity markets (NSE/BSE) are currently in active trading hours.
    Standard regular trading session: Monday to Friday, 09:15 to 15:30 IST (+05:30).
    """
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    now_ist = (dt or datetime.now(timezone.utc)).astimezone(ist_offset)

    # Monday is 0, Sunday is 6
    if now_ist.weekday() >= 5:
        return False

    current_time_minutes = now_ist.hour * 60 + now_ist.minute
    market_open_minutes = 9 * 60 + 15   # 09:15 IST
    market_close_minutes = 15 * 60 + 30  # 15:30 IST

    return market_open_minutes <= current_time_minutes < market_close_minutes


class DemoMarketDataAdapter(MarketDataAdapter):
    """
    Deterministic Synthetic Market Data Provider.
    Generates structured demo prices and historical candles for development.
    """

    # Baseline synthetic price reference points
    DEMO_BASELINES: Dict[str, Dict[str, Decimal]] = {
        "NIFTY 50": {
            "price": Decimal("24850.00"),
            "prev_close": Decimal("24780.00"),
            "change": Decimal("70.00"),
            "change_pct": Decimal("0.28"),
            "open": Decimal("24790.00"),
            "high": Decimal("24910.00"),
            "low": Decimal("24750.00"),
            "close": Decimal("24850.00"),
            "volume": 285000000,
        },
        "NIFTY BANK": {
            "price": Decimal("51200.00"),
            "prev_close": Decimal("51050.00"),
            "change": Decimal("150.00"),
            "change_pct": Decimal("0.29"),
            "open": Decimal("51100.00"),
            "high": Decimal("51350.00"),
            "low": Decimal("50980.00"),
            "close": Decimal("51200.00"),
            "volume": 120000000,
        },
        "SENSEX": {
            "price": Decimal("81650.00"),
            "prev_close": Decimal("81400.00"),
            "change": Decimal("250.00"),
            "change_pct": Decimal("0.31"),
            "open": Decimal("81450.00"),
            "high": Decimal("81800.00"),
            "low": Decimal("81350.00"),
            "close": Decimal("81650.00"),
            "volume": 45000000,
        },
        "INDIA VIX": {
            "price": Decimal("13.45"),
            "prev_close": Decimal("13.80"),
            "change": Decimal("-0.35"),
            "change_pct": Decimal("-2.54"),
            "open": Decimal("13.80"),
            "high": Decimal("14.10"),
            "low": Decimal("13.20"),
            "close": Decimal("13.45"),
            "volume": 0,
        },
        "TCS": {
            "price": Decimal("4180.50"),
            "prev_close": Decimal("4150.00"),
            "change": Decimal("30.50"),
            "change_pct": Decimal("0.73"),
            "open": Decimal("4160.00"),
            "high": Decimal("4205.00"),
            "low": Decimal("4145.00"),
            "close": Decimal("4180.50"),
            "volume": 1850000,
        },
        "INFY": {
            "price": Decimal("1875.25"),
            "prev_close": Decimal("1860.00"),
            "change": Decimal("15.25"),
            "change_pct": Decimal("0.82"),
            "open": Decimal("1862.00"),
            "high": Decimal("1890.00"),
            "low": Decimal("1855.00"),
            "close": Decimal("1875.25"),
            "volume": 4200000,
        },
        "RELIANCE": {
            "price": Decimal("2960.00"),
            "prev_close": Decimal("2945.00"),
            "change": Decimal("15.00"),
            "change_pct": Decimal("0.51"),
            "open": Decimal("2950.00"),
            "high": Decimal("2975.00"),
            "low": Decimal("2935.00"),
            "close": Decimal("2960.00"),
            "volume": 5600000,
        },
        "HDFCBANK": {
            "price": Decimal("1640.00"),
            "prev_close": Decimal("1652.00"),
            "change": Decimal("-12.00"),
            "change_pct": Decimal("-0.73"),
            "open": Decimal("1650.00"),
            "high": Decimal("1658.00"),
            "low": Decimal("1635.00"),
            "close": Decimal("1640.00"),
            "volume": 8900000,
        },
        "ICICIBANK": {
            "price": Decimal("1210.00"),
            "prev_close": Decimal("1202.00"),
            "change": Decimal("8.00"),
            "change_pct": Decimal("0.67"),
            "open": Decimal("1205.00"),
            "high": Decimal("1218.00"),
            "low": Decimal("1198.00"),
            "close": Decimal("1210.00"),
            "volume": 7200000,
        },
        "GOLDBEES": {
            "price": Decimal("64.50"),
            "prev_close": Decimal("64.20"),
            "change": Decimal("0.30"),
            "change_pct": Decimal("0.47"),
            "open": Decimal("64.30"),
            "high": Decimal("64.75"),
            "low": Decimal("64.15"),
            "close": Decimal("64.50"),
            "volume": 3500000,
        },
        "NIFTYBEES": {
            "price": Decimal("268.00"),
            "prev_close": Decimal("267.10"),
            "change": Decimal("0.90"),
            "change_pct": Decimal("0.34"),
            "open": Decimal("267.50"),
            "high": Decimal("269.00"),
            "low": Decimal("266.80"),
            "close": Decimal("268.00"),
            "volume": 6200000,
        },
        "LIQUIDBEES": {
            "price": Decimal("1000.00"),
            "prev_close": Decimal("1000.00"),
            "change": Decimal("0.00"),
            "change_pct": Decimal("0.00"),
            "open": Decimal("1000.00"),
            "high": Decimal("1000.01"),
            "low": Decimal("999.99"),
            "close": Decimal("1000.00"),
            "volume": 1200000,
        },
    }

    def __init__(self, mapper: Optional[InstrumentMapper] = None):
        self.mapper = mapper or default_instrument_mapper

    @property
    def name(self) -> str:
        return "demo"

    @property
    def is_configured(self) -> bool:
        return True

    async def get_quote(self, symbol_or_key: str) -> Optional[MarketQuote]:
        quotes = await self.get_quotes([symbol_or_key])
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        return quotes.get(canonical) or (list(quotes.values())[0] if quotes else None)

    async def get_quotes(self, symbols_or_keys: List[str]) -> Dict[str, MarketQuote]:
        results: Dict[str, MarketQuote] = {}
        trading_active = is_indian_market_hours()
        now_utc = datetime.now(timezone.utc)

        for item in symbols_or_keys:
            canonical = self.mapper.normalize_symbol(item)
            provider_key = self.mapper.get_provider_key(canonical)
            base = self.DEMO_BASELINES.get(canonical)

            if not base:
                # Deterministic synthetic fallback for any unlisted asset
                seed_val = sum(ord(c) for c in canonical) % 500 + 100
                price_dec = Decimal(f"{seed_val}.00")
                base = {
                    "price": price_dec,
                    "prev_close": price_dec,
                    "change": Decimal("0.00"),
                    "change_pct": Decimal("0.00"),
                    "open": price_dec,
                    "high": price_dec,
                    "low": price_dec,
                    "close": price_dec,
                    "volume": 10000,
                }

            quote = MarketQuote(
                symbol=canonical,
                instrument_id=provider_key,
                exchange="NSE" if "BSE" not in provider_key else "BSE",
                price=base["price"],
                previous_close=base["prev_close"],
                change=base["change"],
                change_percent=base["change_pct"],
                volume=int(base["volume"]),
                timestamp=now_utc,
                data_source="demo",
                data_status="synthetic",
                ohlc=OHLCData(
                    open=base["open"],
                    high=base["high"],
                    low=base["low"],
                    close=base["close"],
                ),
                is_market_open=trading_active,
            )
            results[canonical] = quote

        return results

    async def get_historical_data(
        self,
        symbol_or_key: str,
        interval: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        base = self.DEMO_BASELINES.get(canonical, {
            "price": Decimal("1000.00"),
            "prev_close": Decimal("1000.00"),
        })

        base_price = float(base["price"])
        end_date = datetime.now(timezone.utc).date()
        days_to_generate = 60

        candles: List[HistoricalCandle] = []
        for i in range(days_to_generate, 0, -1):
            day_dt = end_date - timedelta(days=i)
            # Skip weekends in synthetic daily history
            if day_dt.weekday() >= 5:
                continue

            # Deterministic wave pattern for testing
            factor = 1.0 + 0.05 * math.sin(i * 0.3)
            close_p = Decimal(f"{base_price * factor:.2f}")
            open_p = Decimal(f"{base_price * (factor - 0.005):.2f}")
            high_p = Decimal(f"{max(float(open_p), float(close_p)) * 1.01:.2f}")
            low_p = Decimal(f"{min(float(open_p), float(close_p)) * 0.99:.2f}")
            vol = int(1000000 + 500000 * math.cos(i * 0.2))

            candle_ts = datetime(day_dt.year, day_dt.month, day_dt.day, 10, 0, tzinfo=timezone.utc)
            candles.append(
                HistoricalCandle(
                    timestamp=candle_ts,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    volume=vol,
                    data_source="demo",
                    data_status="synthetic",
                )
            )

        return candles

    async def get_instruments(self) -> List[InstrumentInfo]:
        return self.mapper.list_all_instruments()

    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        trading_active = is_indian_market_hours()
        status_str = "OPEN" if trading_active else "CLOSED"
        msg = (
            "Indian market continuous trading session active (calculated from IST schedule)"
            if trading_active
            else "Indian markets closed (regular hours: Mon-Fri 09:15-15:30 IST)"
        )
        return MarketStatusResponse(
            exchange=exchange.upper(),
            status=status_str,
            is_trading=trading_active,
            message=msg,
            timestamp=datetime.now(timezone.utc),
            data_source="demo",
            data_status="synthetic",
        )
