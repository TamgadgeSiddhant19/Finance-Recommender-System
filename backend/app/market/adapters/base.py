"""
Abstract Market Data Adapter Interface.
Defines the contract that any live or simulated market data provider must fulfill.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketStatusResponse,
)


class MarketDataAdapter(ABC):
    """
    Abstract interface for market data providers (Demo, Upstox, Yahoo, NSE, etc.).
    Keeps application logic completely decoupled from upstream provider specifics.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier string (e.g. 'demo', 'upstox')."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has all necessary configuration/credentials."""
        pass

    @abstractmethod
    async def get_quote(self, symbol_or_key: str) -> Optional[MarketQuote]:
        """
        Fetch quote for a single symbol or provider key.
        """
        pass

    @abstractmethod
    async def get_quotes(self, symbols_or_keys: List[str]) -> Dict[str, MarketQuote]:
        """
        Fetch quotes for multiple symbols or provider keys.
        """
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        symbol_or_key: str,
        interval: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[HistoricalCandle]:
        """
        Fetch historical OHLCV candle bars for an instrument.
        """
        pass

    @abstractmethod
    async def get_instruments(self) -> List[InstrumentInfo]:
        """
        Fetch available instruments / tradable assets list.
        """
        pass

    @abstractmethod
    async def get_market_status(self, exchange: str = "NSE") -> MarketStatusResponse:
        """
        Fetch operational state (OPEN / CLOSED / PRE_OPEN) for the specified exchange.
        """
        pass
