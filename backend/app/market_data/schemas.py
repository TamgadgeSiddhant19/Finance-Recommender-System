from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# Standard Upstox Instrument Keys for benchmark Indian indices & assets
BENCHMARK_INSTRUMENTS = {
    "NIFTY_50": "NSE_INDEX|Nifty 50",
    "NIFTY_BANK": "NSE_INDEX|Nifty Bank",
    "INDIA_VIX": "NSE_INDEX|India VIX",
    "RELIANCE": "NSE_EQ|INE002A01018",
    "HDFCBANK": "NSE_EQ|INE040A01034",
    "INFY": "NSE_EQ|INE009A01021",
    "TCS": "NSE_EQ|INE467B01029",
    "ICICIBANK": "NSE_EQ|INE090A01021",
}


class OHLCData(BaseModel):
    open: Decimal = Field(..., description="Day open price")
    high: Decimal = Field(..., description="Day high price")
    low: Decimal = Field(..., description="Day low price")
    close: Decimal = Field(..., description="Day close / current LTP price")


class MarketQuote(BaseModel):
    instrument_key: str = Field(..., description="Upstox instrument key, e.g., NSE_INDEX|Nifty 50")
    symbol: str = Field(..., description="Display ticker symbol, e.g. NIFTY 50")
    name: Optional[str] = Field(None, description="Full instrument name")
    ltp: Decimal = Field(..., description="Last traded price in INR")
    previous_close: Decimal = Field(..., description="Previous session close price in INR")
    change: Decimal = Field(..., description="Absolute price change in INR")
    change_percent: Decimal = Field(..., description="Percentage change (+/-)")
    ohlc: Optional[OHLCData] = Field(None, description="Day OHLC data")
    volume: int = Field(default=0, description="Cumulative trading volume")
    timestamp: datetime = Field(..., description="Timestamp of the market data")
    source: str = Field(default="upstox", description="Data provider identifier")
    is_market_open: bool = Field(default=True, description="Whether live market is actively trading")


class HistoricalCandle(BaseModel):
    timestamp: datetime = Field(..., description="Candle start timestamp")
    open: Decimal = Field(..., description="Open price")
    high: Decimal = Field(..., description="High price")
    low: Decimal = Field(..., description="Low price")
    close: Decimal = Field(..., description="Close price")
    volume: int = Field(default=0, description="Volume")
    open_interest: Optional[int] = Field(default=0, description="Open interest")


class MarketStatusResponse(BaseModel):
    exchange: str = Field(default="NSE", description="Exchange code")
    status: str = Field(..., description="OPEN, CLOSED, PRE_OPEN, POST_CLOSE, or OFFLINE")
    is_trading: bool = Field(..., description="Whether live continuous trading is active")
    message: str = Field(..., description="Human readable market operational status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketQuotesBatchResponse(BaseModel):
    quotes: Dict[str, MarketQuote] = Field(..., description="Mapping of instrument key to quote")
    market_status: MarketStatusResponse = Field(..., description="Overall market session status")
    source: str = Field(default="upstox", description="Market data provider")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
