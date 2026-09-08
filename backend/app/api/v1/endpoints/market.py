from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.market_data.schemas import (
    HistoricalCandle,
    MarketQuote,
    MarketQuotesBatchResponse,
    MarketStatusResponse,
)
from app.market_data.service import MarketDataService, get_market_data_service

router = APIRouter()


@router.get(
    "/market/indices",
    response_model=MarketQuotesBatchResponse,
    summary="Get benchmark Indian market indices (NIFTY 50, NIFTY Bank, India VIX)",
)
async def get_market_indices(
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuotesBatchResponse:
    """
    Returns real-time or latest available quotes for core Indian market benchmarks.
    """
    return await service.get_benchmark_indices()


@router.get(
    "/market/quotes",
    response_model=MarketQuotesBatchResponse,
    summary="Get batch market quotes by instrument keys",
)
async def get_market_quotes(
    instruments: List[str] = Query(
        ...,
        description="Instrument keys or comma-separated keys, e.g. 'NSE_INDEX|Nifty 50,NSE_EQ|INE002A01018'",
    ),
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuotesBatchResponse:
    """
    Returns quotes for requested Upstox instrument keys.
    """
    keys = []
    for item in instruments:
        for k in item.split(","):
            if k.strip():
                keys.append(k.strip())
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid instrument key must be provided.",
        )
    return await service.get_quotes(keys)



@router.get(
    "/market/quote/{instrument_key:path}",
    response_model=MarketQuote,
    summary="Get quote for a specific instrument key",
)
async def get_single_market_quote(
    instrument_key: str,
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketQuote:
    """
    Returns quote data for a single instrument key (e.g. NSE_INDEX|Nifty 50).
    """
    quote = await service.get_quote(instrument_key)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote not found for instrument '{instrument_key}'.",
        )
    return quote


@router.get(
    "/market/historical/{instrument_key:path}",
    response_model=List[HistoricalCandle],
    summary="Get historical candle data for an instrument",
)
async def get_historical_market_data(
    instrument_key: str,
    interval: str = Query("day", description="Interval: '1minute', '30minute', 'day', 'week', 'month'"),
    to_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    from_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    service: MarketDataService = Depends(get_market_data_service),
) -> List[HistoricalCandle]:
    """
    Returns historical OHLCV candles for the requested instrument.
    """
    return await service.get_historical_candles(
        instrument_key=instrument_key,
        interval=interval,
        to_date=to_date,
        from_date=from_date,
    )


@router.get(
    "/market/status",
    response_model=MarketStatusResponse,
    summary="Get current Indian exchange operational status",
)
async def get_exchange_market_status(
    exchange: str = Query("NSE", description="Exchange code: NSE or BSE"),
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketStatusResponse:
    """
    Returns whether exchange is currently open for trading.
    """
    return await service.get_market_status(exchange=exchange)
