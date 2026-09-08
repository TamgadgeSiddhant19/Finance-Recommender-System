from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.market_data.provider import BaseMarketDataProvider
from app.market_data.schemas import (
    BENCHMARK_INSTRUMENTS,
    HistoricalCandle,
    MarketQuote,
    MarketQuotesBatchResponse,
    MarketStatusResponse,
)
from app.market_data.upstox_client import UpstoxMarketDataProvider


class MarketDataService:
    """
    High-level business service for Indian market data, benchmarks, and quotations.
    """

    def __init__(self, provider: Optional[BaseMarketDataProvider] = None):
        self.provider: BaseMarketDataProvider = provider or UpstoxMarketDataProvider()
        self._cache: Dict[str, tuple[datetime, MarketQuote]] = {}
        self._cache_ttl_seconds = 15  # 15-second TTL cache for quote snapshot deduplication

    async def get_benchmark_indices(self) -> MarketQuotesBatchResponse:
        """
        Retrieves live / latest benchmark quotes for NIFTY 50, NIFTY Bank, and India VIX.
        """
        benchmark_keys = [
            BENCHMARK_INSTRUMENTS["NIFTY_50"],
            BENCHMARK_INSTRUMENTS["NIFTY_BANK"],
            BENCHMARK_INSTRUMENTS["INDIA_VIX"],
        ]
        return await self.get_quotes(benchmark_keys)

    async def get_quotes(self, instrument_keys: List[str]) -> MarketQuotesBatchResponse:
        """
        Fetch quotes for a list of instruments with in-memory TTL caching.
        """
        now = datetime.now(timezone.utc)
        cached_quotes: Dict[str, MarketQuote] = {}
        keys_to_fetch: List[str] = []

        for key in instrument_keys:
            if key in self._cache:
                cached_time, quote = self._cache[key]
                if (now - cached_time).total_seconds() < self._cache_ttl_seconds:
                    cached_quotes[key] = quote
                    continue
            keys_to_fetch.append(key)

        if keys_to_fetch:
            fetched = await self.provider.get_quotes(keys_to_fetch)
            for k, q in fetched.items():
                self._cache[k] = (now, q)
                cached_quotes[k] = q

        status = await self.provider.get_market_status("NSE")

        return MarketQuotesBatchResponse(
            quotes=cached_quotes,
            market_status=status,
            source=self.provider.name,
            retrieved_at=now,
        )

    async def get_quote(self, instrument_key: str) -> Optional[MarketQuote]:
        """
        Fetch single quote for an instrument key.
        """
        batch = await self.get_quotes([instrument_key])
        return batch.quotes.get(instrument_key)

    async def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        """
        Fetch historical candle series.
        """
        return await self.provider.get_historical_candles(
            instrument_key=instrument_key,
            interval=interval,
            to_date=to_date,
            from_date=from_date,
        )

    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        """
        Fetch exchange trading operational status.
        """
        return await self.provider.get_market_status(exchange=exchange)


# Default singleton instance
_market_service_instance: Optional[MarketDataService] = None


def get_market_data_service() -> MarketDataService:
    global _market_service_instance
    if _market_service_instance is None:
        _market_service_instance = MarketDataService()
    return _market_service_instance
