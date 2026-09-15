"""
Market Data API Endpoints.
Provides normalized real-time and historical market data through the provider-independent MarketDataService.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.market.exceptions import MarketDataError
from app.market.schemas import (
    HistoricalCandle,
    InstrumentInfo,
    MarketQuote,
    MarketQuotesBatchResponse,
    MarketStatusResponse,
)
from app.market.service import MarketDataService, get_market_data_service

router = APIRouter()


@router.get(
    "/market/status",
    response_model=MarketStatusResponse,
    summary="Get current Indian exchange operational status",
)
async def get_market_status(
    exchange: str = Query("NSE", description="Exchange code: NSE or BSE"),
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketStatusResponse:
    """
    Returns whether exchange is currently open for trading.
    Includes data_source and data_status provenance.
    """
    return await service.get_market_status(exchange=exchange)


@router.get(
    "/market/instruments",
    response_model=List[InstrumentInfo],
    summary="List available/mapped market instruments",
)
async def get_instruments(
    service: MarketDataService = Depends(get_market_data_service),
) -> List[InstrumentInfo]:
    """
    Returns metadata list of tradable equity symbols, benchmark indices, and ETFs.
    """
    return await service.get_instruments()


@router.get(
    "/market/indices",
    response_model=MarketQuotesBatchResponse,
    summary="Get benchmark Indian market indices (NIFTY 50, NIFTY Bank, India VIX)",
)
async def get_market_indices(
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuotesBatchResponse:
    """
    Returns normalized quotes for core Indian market benchmarks.
    """
    return await service.get_benchmark_indices()


@router.get(
    "/market/quotes",
    response_model=MarketQuotesBatchResponse,
    summary="Get batch market quotes by symbols or instrument keys",
)
async def get_market_quotes(
    instruments: List[str] = Query(
        ...,
        description="Symbols or instrument keys, e.g. 'TCS,INFY,NIFTY 50' or 'NSE_INDEX|Nifty 50'",
    ),
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuotesBatchResponse:
    """
    Returns quotes for requested symbols or keys.
    """
    keys = []
    for item in instruments:
        for k in item.split(","):
            if k.strip():
                keys.append(k.strip())
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid symbol or instrument key must be provided.",
        )
    return await service.get_quotes(keys)


@router.get(
    "/market/quote/{symbol:path}",
    response_model=MarketQuote,
    summary="Get quote for a specific symbol or instrument key",
)
async def get_single_market_quote(
    symbol: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuote:
    """
    Returns normalized quote data for a symbol (e.g. 'TCS', 'INFY', 'NIFTY 50')
    or provider key (e.g. 'NSE_INDEX|Nifty 50').
    """
    try:
        quote = await service.get_quote(symbol)
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quote not found for symbol or instrument '{symbol}'.",
            )
        return quote
    except MarketDataError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.get(
    "/market/history/{symbol:path}",
    response_model=List[HistoricalCandle],
    summary="Get historical candle data for a symbol",
)
async def get_historical_market_data(
    symbol: str,
    interval: str = Query("day", description="Interval: '1minute', '30minute', 'day', 'week', 'month'"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    service: MarketDataService = Depends(get_market_data_service),
) -> List[HistoricalCandle]:
    """
    Returns historical OHLCV candle bars for the requested symbol.
    """
    return await service.get_historical_candles(
        symbol_or_key=symbol,
        interval=interval,
        to_date=to_date,
        from_date=from_date,
    )


# Backward compatibility alias for /market/historical/{instrument_key}
@router.get(
    "/market/historical/{instrument_key:path}",
    response_model=List[HistoricalCandle],
    include_in_schema=False,
)
async def get_historical_market_data_legacy(
    instrument_key: str,
    interval: str = Query("day"),
    to_date: Optional[str] = None,
    from_date: Optional[str] = None,
    service: MarketDataService = Depends(get_market_data_service),
) -> List[HistoricalCandle]:
    return await service.get_historical_candles(
        symbol_or_key=instrument_key,
        interval=interval,
        to_date=to_date,
        from_date=from_date,
    )
