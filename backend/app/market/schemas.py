"""
Market Data Pydantic Schemas.
Enforces high-precision Decimal types and explicit source/status provenance tracking.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class OHLCData(BaseModel):
    """Normalized open, high, low, close price snapshot."""

    open: Decimal = Field(..., description="Day opening price")
    high: Decimal = Field(..., description="Day high price")
    low: Decimal = Field(..., description="Day low price")
    close: Decimal = Field(..., description="Day close / last evaluated price")

    model_config = ConfigDict(from_attributes=True)


class MarketQuote(BaseModel):
    """
    Normalized real-time or snapshot market quote.
    Maintains rigorous provenance (data_source and data_status) to prevent
    synthetic demo data from ever being misrepresented as live financial market data.
    """

    symbol: str = Field(..., description="Internal canonical symbol, e.g., 'TCS' or 'NIFTY 50'")
    instrument_id: str = Field(..., description="Provider-specific instrument identifier, e.g., 'NSE_INDEX|Nifty 50'")
    exchange: str = Field(default="NSE", description="Exchange code, e.g. NSE, BSE")
    price: Decimal = Field(..., description="Last traded price (LTP)")
    previous_close: Decimal = Field(..., description="Previous trading day closing price")
    change: Decimal = Field(..., description="Absolute change from previous close (price - previous_close)")
    change_percent: Decimal = Field(..., description="Percentage change from previous close")
    volume: int = Field(default=0, description="Cumulative day volume")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the quote in UTC",
    )
    data_source: str = Field(
        ...,
        description="Origin identifier of market data, e.g. 'demo', 'upstox'",
    )
    data_status: str = Field(
        ...,
        description="Freshness/nature status: 'synthetic', 'live', 'delayed', 'offline'",
    )
    ohlc: Optional[OHLCData] = Field(default=None, description="Day OHLC metrics")
    is_market_open: bool = Field(default=False, description="Whether the trading session was active at quote time")

    # Backward-compatible serialized fields
    @computed_field
    @property
    def ltp(self) -> Decimal:
        return self.price

    @computed_field
    @property
    def instrument_key(self) -> str:
        return self.instrument_id

    @computed_field
    @property
    def source(self) -> str:
        return self.data_source

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HistoricalCandle(BaseModel):
    """
    Normalized OHLCV historical candle bar.
    """

    timestamp: datetime = Field(..., description="Start timestamp of the candle bar in UTC")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price during interval")
    low: Decimal = Field(..., description="Lowest price during interval")
    close: Decimal = Field(..., description="Closing price during interval")
    volume: int = Field(default=0, description="Volume traded during interval")
    open_interest: Optional[int] = Field(default=None, description="Open interest where applicable (derivatives)")
    data_source: str = Field(..., description="Data provider identifier: 'demo', 'upstox'")
    data_status: str = Field(default="synthetic", description="'synthetic', 'historical', 'live'")

    model_config = ConfigDict(from_attributes=True)


class InstrumentInfo(BaseModel):
    """
    Metadata representation of a market tradable asset or benchmark.
    """

    symbol: str = Field(..., description="Internal canonical symbol, e.g. 'TCS'")
    name: str = Field(..., description="Human-readable asset or fund name")
    exchange: str = Field(default="NSE", description="Exchange code (NSE / BSE / MCX)")
    instrument_type: str = Field(..., description="Type: 'EQUITY', 'INDEX', 'MUTUAL_FUND', 'ETF', 'COMMODITY'")
    provider_key: str = Field(..., description="Provider-specific identifier/key")
    is_active: bool = Field(default=True, description="Whether instrument is actively traded")
    data_source: str = Field(default="internal_mapping", description="Mapping origin source")

    model_config = ConfigDict(from_attributes=True)


class MarketStatusResponse(BaseModel):
    """
    Current exchange operational state.
    """

    exchange: str = Field(default="NSE", description="Exchange identifier")
    status: str = Field(..., description="'OPEN', 'CLOSED', 'PRE_OPEN', 'AFTER_HOURS'")
    is_trading: bool = Field(..., description="True if continuous trading session is active")
    message: str = Field(..., description="Informative status message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the status check in UTC",
    )
    data_source: str = Field(default="demo", description="Origin of market status calculation")
    data_status: str = Field(default="synthetic", description="'synthetic', 'live', 'offline'")

    model_config = ConfigDict(from_attributes=True)


class MarketQuotesBatchResponse(BaseModel):
    """
    Batch quotes response for indices or multiple instruments.
    """

    quotes: Dict[str, MarketQuote] = Field(default_factory=dict, description="Dictionary of symbol -> MarketQuote")
    market_status: Optional[MarketStatusResponse] = Field(default=None, description="Exchange status")
    data_source: str = Field(default="demo", description="Active market data provider")
    data_status: str = Field(default="synthetic", description="Overall data status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp in UTC",
    )

    # Backward-compatible serialized fields
    @computed_field
    @property
    def source(self) -> str:
        return self.data_source

    @computed_field
    @property
    def retrieved_at(self) -> datetime:
        return self.timestamp

    model_config = ConfigDict(from_attributes=True)
