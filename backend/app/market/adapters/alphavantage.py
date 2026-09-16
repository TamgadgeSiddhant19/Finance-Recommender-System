"""
Alpha Vantage API Market Data Adapter.
Implements the MarketDataAdapter interface for Alpha Vantage financial data services.

CRITICAL INTEGRITY RULES:
- When real API data is returned, data_source="alphavantage" and data_status="historical" or "live".
- When API key is unconfigured or rate limited, returns explicit unconfigured/unavailable status without fabricating synthetic data.
"""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Dict, List, Optional
import httpx

from app.core.config import settings
from app.market.adapters.base import MarketDataAdapter
from app.market.adapters.demo import is_indian_market_hours
from app.market.instrument_mapping import InstrumentMapper, default_instrument_mapper
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketStatusResponse,
    OHLCData,
)

logger = logging.getLogger(__name__)


class AlphaVantageMarketDataAdapter(MarketDataAdapter):
    """
    Market Data Adapter communicating with Alpha Vantage API.
    Provides standard quotes and historical daily candle time series.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mapper: Optional[InstrumentMapper] = None,
    ):
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        self.base_url = (base_url or settings.ALPHA_VANTAGE_BASE_URL).rstrip("/")
        self.mapper = mapper or default_instrument_mapper

    @property
    def name(self) -> str:
        return "alphavantage"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "demo")

    async def get_quote(self, symbol_or_key: str) -> Optional[MarketQuote]:
        quotes = await self.get_quotes([symbol_or_key])
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        return quotes.get(canonical) or (list(quotes.values())[0] if quotes else None)

    async def get_quotes(self, symbols_or_keys: List[str]) -> Dict[str, MarketQuote]:
        if not symbols_or_keys:
            return {}

        results: Dict[str, MarketQuote] = {}

        if not self.is_configured:
            logger.info("Alpha Vantage API key unconfigured. Returning unconfigured status.")
            return self._build_unconfigured_quotes(symbols_or_keys)

        async with httpx.AsyncClient(timeout=10.0) as client:
            for item in symbols_or_keys:
                canonical = self.mapper.normalize_symbol(item)
                provider_key = self.mapper.get_provider_key(canonical)
                # Map Indian symbols to BSE/BSE format if needed, or query direct ticker
                av_symbol = self._format_av_symbol(canonical, provider_key)

                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": av_symbol,
                    "apikey": self.api_key,
                }

                try:
                    resp = await client.get(self.base_url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        g_quote = data.get("Global Quote", {})
                        if g_quote and "05. price" in g_quote:
                            price = Decimal(str(g_quote.get("05. price", "0.00")))
                            prev_close = Decimal(str(g_quote.get("08. previous close", "0.00")))
                            change = Decimal(str(g_quote.get("09. change", "0.00")))
                            change_pct_str = g_quote.get("10. change percent", "0.0%").replace("%", "")
                            change_pct = Decimal(str(change_pct_str)) if change_pct_str else Decimal("0.00")
                            open_p = Decimal(str(g_quote.get("02. open", price)))
                            high_p = Decimal(str(g_quote.get("03. high", price)))
                            low_p = Decimal(str(g_quote.get("04. low", price)))
                            vol = int(g_quote.get("06. volume", 0))

                            results[canonical] = MarketQuote(
                                symbol=canonical,
                                instrument_id=provider_key,
                                exchange="BSE" if ".BSE" in av_symbol else "NSE",
                                price=price,
                                previous_close=prev_close,
                                change=change,
                                change_percent=change_pct,
                                volume=vol,
                                timestamp=datetime.now(timezone.utc),
                                data_source="alphavantage",
                                data_status="live",
                                ohlc=OHLCData(open=open_p, high=high_p, low=low_p, close=price),
                                is_market_open=is_indian_market_hours(),
                            )
                        else:
                            # Note limit or empty response
                            results[canonical] = self._build_single_unconfigured_quote(canonical, provider_key, status="unavailable")
                    else:
                        results[canonical] = self._build_single_unconfigured_quote(canonical, provider_key, status="offline")
                except Exception as e:
                    logger.warning(f"Alpha Vantage quote fetch failed for {canonical}: {e}")
                    results[canonical] = self._build_single_unconfigured_quote(canonical, provider_key, status="offline")

        return results

    async def get_historical_data(
        self,
        symbol_or_key: str,
        interval: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        if not self.is_configured:
            logger.info("Alpha Vantage API key unconfigured for historical data.")
            return []

        canonical = self.mapper.normalize_symbol(symbol_or_key)
        provider_key = self.mapper.get_provider_key(canonical)
        av_symbol = self._format_av_symbol(canonical, provider_key)

    def _parse_time_series_daily(
        self,
        data: dict,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        """Parses Alpha Vantage TIME_SERIES_DAILY JSON output into normalized HistoricalCandle objects."""
        candles: List[HistoricalCandle] = []
        ts_data = data.get("Time Series (Daily)", {})
        for date_str, bar in sorted(ts_data.items()):
            if from_date and date_str < from_date:
                continue
            if to_date and date_str > to_date:
                continue

            dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            candles.append(
                HistoricalCandle(
                    timestamp=dt,
                    open=Decimal(str(bar.get("1. open", "0.00"))),
                    high=Decimal(str(bar.get("2. high", "0.00"))),
                    low=Decimal(str(bar.get("3. low", "0.00"))),
                    close=Decimal(str(bar.get("4. close", "0.00"))),
                    volume=int(bar.get("5. volume", 0)),
                    data_source="alphavantage",
                    data_status="historical",
                )
            )
        return candles

    async def get_historical_data(
        self,
        symbol_or_key: str,
        interval: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        if not self.is_configured:
            logger.info("Alpha Vantage API key unconfigured for historical data.")
            return []

        canonical = self.mapper.normalize_symbol(symbol_or_key)
        provider_key = self.mapper.get_provider_key(canonical)
        av_symbol = self._format_av_symbol(canonical, provider_key)

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": av_symbol,
            "outputsize": "full",
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return self._parse_time_series_daily(data, from_date=from_date, to_date=to_date)
        except Exception as e:
            logger.error(f"Failed to fetch historical candles from Alpha Vantage for {canonical}: {e}")

        return []

    async def get_instruments(self) -> List[InstrumentInfo]:
        return self.mapper.list_all_instruments()

    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        trading_active = is_indian_market_hours()
        status_str = "OPEN" if trading_active else "CLOSED"
        return MarketStatusResponse(
            exchange=exchange.upper(),
            status=status_str,
            is_trading=trading_active,
            message="Alpha Vantage market status derived from Indian trading schedule (IST 09:15-15:30)",
            timestamp=datetime.now(timezone.utc),
            data_source="alphavantage",
            data_status="live" if self.is_configured else "unconfigured",
        )

    def _format_av_symbol(self, canonical: str, provider_key: str) -> str:
        """Formats instrument for Alpha Vantage (e.g. RELIANCE.BSE, INFY.BSE)."""
        clean_sym = canonical.upper().replace(" ", "")
        if clean_sym in {"NIFTY50", "NIFTY50-INDX", "NIFTY"}:
            return "^NSEI"
        if clean_sym in {"SENSEX", "BSESENSEX"}:
            return "^BSESN"
        if clean_sym.endswith("-EQ") or clean_sym.endswith("-INDX"):
            clean_sym = clean_sym.split("-")[0]
        # Default suffix for Indian stocks in Alpha Vantage
        return f"{clean_sym}.BSE"

    def _build_unconfigured_quotes(self, symbols: List[str]) -> Dict[str, MarketQuote]:
        results: Dict[str, MarketQuote] = {}
        for s in symbols:
            canonical = self.mapper.normalize_symbol(s)
            provider_key = self.mapper.get_provider_key(canonical)
            results[canonical] = self._build_single_unconfigured_quote(canonical, provider_key, status="unconfigured")
        return results

    def _build_single_unconfigured_quote(self, canonical: str, provider_key: str, status: str = "unconfigured") -> MarketQuote:
        zero = Decimal("0.00")
        return MarketQuote(
            symbol=canonical,
            instrument_id=provider_key,
            exchange="NSE",
            price=zero,
            previous_close=zero,
            change=zero,
            change_percent=zero,
            volume=0,
            timestamp=datetime.now(timezone.utc),
            data_source="alphavantage",
            data_status=status,
            ohlc=OHLCData(open=zero, high=zero, low=zero, close=zero),
            is_market_open=is_indian_market_hours(),
        )
