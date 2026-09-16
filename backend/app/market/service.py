"""
Market Data Orchestration Service.
Abstracts all market data provider selection, caching, and normalization.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.market.adapters.alphavantage import AlphaVantageMarketDataAdapter
from app.market.adapters.base import MarketDataAdapter
from app.market.adapters.demo import DemoMarketDataAdapter
from app.market.adapters.upstox import UpstoxMarketDataAdapter
from app.market.instrument_mapping import InstrumentMapper, default_instrument_mapper
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketQuotesBatchResponse,
    MarketStatusResponse,
)

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Central Market Data Service for Artha AI.
    Ensures that domain layers (recommendations, RAG, frontend) remain
    completely decoupled from upstream data provider implementation details.
    """

    BENCHMARK_SYMBOLS = ["NIFTY 50", "NIFTY BANK", "INDIA VIX"]

    def __init__(
        self,
        adapter: Optional[MarketDataAdapter] = None,
        mapper: Optional[InstrumentMapper] = None,
        cache_ttl_seconds: int = 5,
    ):
        self.mapper = mapper or default_instrument_mapper
        self.adapter = adapter or self._resolve_adapter()
        self.cache_ttl = cache_ttl_seconds

        # In-memory short-lived quote cache: {symbol: (quote, cached_at_timestamp)}
        self._quote_cache: Dict[str, tuple[MarketQuote, float]] = {}

    def _resolve_adapter(self) -> MarketDataAdapter:
        provider_name = getattr(settings, "MARKET_DATA_PROVIDER", "demo").lower()
        if provider_name == "alphavantage":
            logger.info("Initializing AlphaVantageMarketDataAdapter...")
            return AlphaVantageMarketDataAdapter(mapper=self.mapper)
        elif provider_name == "upstox":
            logger.info("Initializing UpstoxMarketDataAdapter...")
            return UpstoxMarketDataAdapter(mapper=self.mapper)
        logger.info("Initializing DemoMarketDataAdapter (default provider)...")
        return DemoMarketDataAdapter(mapper=self.mapper)

    @property
    def provider_name(self) -> str:
        return self.adapter.name

    @property
    def is_configured(self) -> bool:
        return self.adapter.is_configured

    async def get_quote(self, symbol_or_key: str) -> Optional[MarketQuote]:
        """
        Fetch normalized quote for a single symbol or provider key.
        """
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        now_ts = datetime.now(timezone.utc).timestamp()

        # Cache check
        if canonical in self._quote_cache:
            cached_quote, cached_time = self._quote_cache[canonical]
            if now_ts - cached_time < self.cache_ttl:
                return cached_quote

        quote = await self.adapter.get_quote(canonical)
        if quote:
            self._quote_cache[canonical] = (quote, now_ts)
        return quote

    async def get_quotes(self, symbols_or_keys: List[str]) -> MarketQuotesBatchResponse:
        """
        Fetch normalized quotes for a list of symbols or provider keys.
        """
        if not symbols_or_keys:
            return MarketQuotesBatchResponse(
                quotes={},
                data_source=self.adapter.name,
                data_status="synthetic" if self.adapter.name == "demo" else "live",
            )

        now_ts = datetime.now(timezone.utc).timestamp()
        results: Dict[str, MarketQuote] = {}
        missing_symbols: List[str] = []

        for item in symbols_or_keys:
            canonical = self.mapper.normalize_symbol(item)
            if canonical in self._quote_cache:
                cached_quote, cached_time = self._quote_cache[canonical]
                if now_ts - cached_time < self.cache_ttl:
                    results[canonical] = cached_quote
                    continue
            missing_symbols.append(canonical)

        if missing_symbols:
            fetched_quotes = await self.adapter.get_quotes(missing_symbols)
            for k, q in fetched_quotes.items():
                results[k] = q
                self._quote_cache[k] = (q, now_ts)

        status = await self.adapter.get_market_status("NSE")

        # Map requested query items and canonical symbols to their quote
        final_quotes: Dict[str, MarketQuote] = {}
        for item in symbols_or_keys:
            canonical = self.mapper.normalize_symbol(item)
            if canonical in results:
                final_quotes[item] = results[canonical]
                final_quotes[canonical] = results[canonical]

        return MarketQuotesBatchResponse(
            quotes=final_quotes,
            market_status=status,
            data_source=self.adapter.name,
            data_status=status.data_status,
            timestamp=datetime.now(timezone.utc),
        )

    async def get_benchmark_indices(self) -> MarketQuotesBatchResponse:
        """
        Fetch quotes for core Indian benchmark indices (NIFTY 50, NIFTY Bank, INDIA VIX).
        """
        return await self.get_quotes(self.BENCHMARK_SYMBOLS)

    async def get_historical_candles(
        self,
        symbol_or_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        """
        Fetch historical candle bars.
        """
        canonical = self.mapper.normalize_symbol(symbol_or_key)
        return await self.adapter.get_historical_data(
            symbol_or_key=canonical,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
        )

    async def get_instruments(self) -> List[InstrumentInfo]:
        """
        Fetch all mapped/available tradable instruments.
        """
        return await self.adapter.get_instruments()

    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        """
        Fetch current exchange operational status.
        """
        return await self.adapter.get_market_status(exchange=exchange)


# Singleton service instance
_global_market_service: Optional[MarketDataService] = None


def get_market_data_service() -> MarketDataService:
    """FastAPI Dependency Provider for MarketDataService."""
    global _global_market_service
    if _global_market_service is None:
        _global_market_service = MarketDataService()
    return _global_market_service
