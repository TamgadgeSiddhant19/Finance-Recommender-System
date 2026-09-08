from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.market_data.schemas import (
    HistoricalCandle,
    MarketQuote,
    MarketStatusResponse,
)


class BaseMarketDataProvider(ABC):
    """
    Abstract interface for market data providers (Upstox, Yahoo, NSE, etc.).
    Keeps business logic completely decoupled from upstream provider specifics.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if valid API credentials/tokens are configured."""
        pass

    @abstractmethod
    async def get_quotes(self, instrument_keys: List[str]) -> Dict[str, MarketQuote]:
        """
        Fetch real-time or latest available quotes for requested instrument keys.
        """
        pass

    @abstractmethod
    async def get_historical_candles(
        self,
        instrument_key: str,
        interval: str = "day",
        to_date: Optional[str] = None,
        from_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        """
        Fetch historical candle data for a given instrument.
        """
        pass

    @abstractmethod
    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        """
        Fetch current market operational status (OPEN, CLOSED, etc.).
        """
        pass
