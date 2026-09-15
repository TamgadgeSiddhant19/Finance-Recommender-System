"""
Provider-Independent Market Data Module.
"""

from app.market.adapters.base import MarketDataAdapter
from app.market.adapters.demo import DemoMarketDataAdapter
from app.market.adapters.upstox import UpstoxMarketDataAdapter
from app.market.exceptions import (
    InstrumentNotFoundError,
    MarketDataError,
    ProviderAuthenticationError,
    ProviderUnavailableError,
)
from app.market.instrument_mapping import InstrumentMapper, default_instrument_mapper
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketQuotesBatchResponse,
    MarketStatusResponse,
    OHLCData,
)
from app.market.service import MarketDataService, get_market_data_service

__all__ = [
    "MarketDataAdapter",
    "DemoMarketDataAdapter",
    "UpstoxMarketDataAdapter",
    "MarketDataError",
    "InstrumentNotFoundError",
    "ProviderUnavailableError",
    "ProviderAuthenticationError",
    "InstrumentMapper",
    "default_instrument_mapper",
    "MarketQuote",
    "HistoricalCandle",
    "InstrumentInfo",
    "MarketStatusResponse",
    "MarketQuotesBatchResponse",
    "OHLCData",
    "MarketDataService",
    "get_market_data_service",
]
