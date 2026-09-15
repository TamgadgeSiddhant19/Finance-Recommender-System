"""
Upstox API v2 Market Data Adapter.
Implements the MarketDataAdapter interface for Upstox broker API.
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


class UpstoxMarketDataAdapter(MarketDataAdapter):
    """
    Market Data Adapter communicating directly with Upstox API v2.
    Decoupled from application domain logic through the MarketDataAdapter interface.
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        api_base_url: Optional[str] = None,
        mapper: Optional[InstrumentMapper] = None,
    ):
        self.base_url = (api_base_url or settings.UPSTOX_API_BASE_URL).rstrip("/")
        self.access_token = access_token or settings.UPSTOX_ACCESS_TOKEN
        self.mapper = mapper or default_instrument_mapper

    @property
    def name(self) -> str:
        return "upstox"

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.access_token.strip())

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token or ''}",
        }

    async def get_quote(self, symbol_or_key: str) -> Optional[MarketQuote]:
        quotes = await self.get_quotes([symbol_or_key])
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        return quotes.get(canonical) or (list(quotes.values())[0] if quotes else None)

    async def get_quotes(self, symbols_or_keys: List[str]) -> Dict[str, MarketQuote]:
        if not symbols_or_keys:
            return {}

        provider_keys = [self.mapper.get_provider_key(s) for s in symbols_or_keys]

        if not self.is_configured:
            logger.info("Upstox access token unconfigured. Returning unconfigured status.")
            return self._build_unconfigured_quotes(symbols_or_keys, error_msg=None)

        url = f"{self.base_url}/market-quote/quotes"
        params = {"instrument_key": ",".join(provider_keys)}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, headers=self._get_headers(), params=params)

                if response.status_code == 401:
                    logger.warning("Upstox API returned 401 Unauthorized. Access token expired or invalid.")
                    return self._build_unconfigured_quotes(symbols_or_keys, error_msg="Upstox token expired")

                if response.status_code != 200:
                    logger.error(f"Upstox API quote error: HTTP {response.status_code} - {response.text}")
                    return self._build_unconfigured_quotes(symbols_or_keys, error_msg=f"Upstox API error {response.status_code}")

                data = response.json()
                return self._parse_upstox_quotes_payload(data, symbols_or_keys)

        except Exception as e:
            logger.error(f"Failed to connect to Upstox API: {str(e)}")
            return self._build_unconfigured_quotes(symbols_or_keys, error_msg=str(e))

    def _parse_upstox_quotes_payload(
        self, payload: dict, requested_symbols: List[str]
    ) -> Dict[str, MarketQuote]:
        results: Dict[str, MarketQuote] = {}
        data = payload.get("data", {})
        trading_active = is_indian_market_hours()

        for requested in requested_symbols:
            canonical = self.mapper.normalize_symbol(requested)
            provider_key = self.mapper.get_provider_key(canonical)

            # Upstox returns keys with colon ':' instead of pipe '|', e.g. NSE_INDEX:Nifty 50
            colon_key = provider_key.replace("|", ":")
            quote_data = data.get(provider_key) or data.get(colon_key)

            if not quote_data:
                continue

            last_price = Decimal(str(quote_data.get("last_price", 0.0)))
            ohlc = quote_data.get("ohlc", {})
            open_p = Decimal(str(ohlc.get("open", last_price)))
            high_p = Decimal(str(ohlc.get("high", last_price)))
            low_p = Decimal(str(ohlc.get("low", last_price)))
            close_p = Decimal(str(ohlc.get("close", last_price)))
            prev_close = close_p if close_p > 0 else last_price

            change = last_price - prev_close
            change_pct = (change / prev_close * Decimal("100")) if prev_close > 0 else Decimal("0.00")
            volume = int(quote_data.get("volume", 0))

            results[canonical] = MarketQuote(
                symbol=canonical,
                instrument_id=provider_key,
                exchange="NSE" if "BSE" not in provider_key else "BSE",
                price=last_price,
                previous_close=prev_close,
                change=change,
                change_percent=change_pct,
                volume=volume,
                timestamp=datetime.now(timezone.utc),
                data_source="upstox",
                data_status="live",
                ohlc=OHLCData(open=open_p, high=high_p, low=low_p, close=close_p),
                is_market_open=trading_active,
            )

        return results

    def _build_unconfigured_quotes(
        self, requested_symbols: List[str], error_msg: Optional[str] = None
    ) -> Dict[str, MarketQuote]:
        trading_active = is_indian_market_hours()
        results: Dict[str, MarketQuote] = {}

        for sym in requested_symbols:
            canonical = self.mapper.normalize_symbol(sym)
            provider_key = self.mapper.get_provider_key(canonical)
            zero = Decimal("0.00")

            results[canonical] = MarketQuote(
                symbol=canonical,
                instrument_id=provider_key,
                exchange="NSE",
                price=zero,
                previous_close=zero,
                change=zero,
                change_percent=zero,
                volume=0,
                timestamp=datetime.now(timezone.utc),
                data_source="upstox",
                data_status="offline" if error_msg else "unconfigured",
                ohlc=OHLCData(open=zero, high=zero, low=zero, close=zero),
                is_market_open=trading_active,
            )

        return results

    async def get_historical_data(
        self,
        symbol_or_key: str,
        interval: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        if not self.is_configured:
            logger.info("Upstox unconfigured for historical data.")
            return []

        canonical = self.mapper.normalize_symbol(symbol_or_key)
        provider_key = self.mapper.get_provider_key(canonical)

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        to_d = to_date or today_str
        from_d = from_date or "2024-01-01"

        url = f"{self.base_url}/historical-candle/{provider_key}/{interval}/{to_d}/{from_d}"
        candles: List[HistoricalCandle] = []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    raw_candles = data.get("data", {}).get("candles", [])
                    for c in raw_candles:
                        if len(c) >= 6:
                            candles.append(
                                HistoricalCandle(
                                    timestamp=datetime.fromisoformat(c[0]),
                                    open=Decimal(str(c[1])),
                                    high=Decimal(str(c[2])),
                                    low=Decimal(str(c[3])),
                                    close=Decimal(str(c[4])),
                                    volume=int(c[5]),
                                    open_interest=int(c[6]) if len(c) > 6 else None,
                                    data_source="upstox",
                                    data_status="historical",
                                )
                            )
        except Exception as e:
            logger.error(f"Failed to fetch historical candles from Upstox: {str(e)}")

        return candles

    async def get_instruments(self) -> List[InstrumentInfo]:
        return self.mapper.list_all_instruments()

    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        trading_active = is_indian_market_hours()

        if not self.is_configured:
            status_text = "OPEN" if trading_active else "CLOSED"
            return MarketStatusResponse(
                exchange=exchange,
                status=status_text,
                is_trading=trading_active,
                message="Upstox unconfigured - calculated from IST trading hours",
                timestamp=datetime.now(timezone.utc),
                data_source="upstox",
                data_status="unconfigured",
            )

        url = f"{self.base_url}/market/status/{exchange}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    raw_status = data.get("status", "CLOSED").upper()
                    return MarketStatusResponse(
                        exchange=exchange,
                        status=raw_status,
                        is_trading=raw_status == "OPEN",
                        message=f"Upstox NSE Market Status: {raw_status}",
                        timestamp=datetime.now(timezone.utc),
                        data_source="upstox",
                        data_status="live",
                    )
        except Exception as e:
            logger.warning(f"Could not fetch market status from Upstox: {str(e)}")

        status_text = "OPEN" if trading_active else "CLOSED"
        return MarketStatusResponse(
            exchange=exchange,
            status=status_text,
            is_trading=trading_active,
            message="Upstox offline - fallback to IST schedule",
            timestamp=datetime.now(timezone.utc),
            data_source="upstox",
            data_status="offline",
        )
