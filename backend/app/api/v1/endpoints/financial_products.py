from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.financial_data.ingestion import IngestionService
from app.financial_data.models import FinancialProduct, MarketData
from app.financial_data.repository import FinancialProductRepository
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductResponse,
    IngestionSummary,
    MarketDataResponse,
    ProductRiskLevel,
    ProductType,
)

router = APIRouter()


@router.get(
    "/financial-products",
    response_model=List[FinancialProductResponse],
    summary="List all financial products",
)
async def list_products(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[FinancialProduct]:
    """
    Retrieve paginated list of all financial products in the catalog.
    """
    repo = FinancialProductRepository(db)
    return await repo.list_products(skip=skip, limit=limit)


@router.get(
    "/financial-products/filter",
    response_model=List[FinancialProductResponse],
    summary="Filter financial products by criteria",
)
async def filter_products(
    asset_class: Optional[AssetClass] = Query(None, description="Filter by asset class"),
    product_type: Optional[ProductType] = Query(None, description="Filter by product type"),
    risk_level: Optional[ProductRiskLevel] = Query(None, description="Filter by risk level"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: AsyncSession = Depends(get_db),
) -> List[FinancialProduct]:
    """
    Filter financial products by broad asset class, product type, and risk level.
    """
    repo = FinancialProductRepository(db)
    return await repo.filter_products(
        asset_class=asset_class,
        product_type=product_type,
        risk_level=risk_level,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/financial-products/{product_id}",
    response_model=FinancialProductResponse,
    summary="Get financial product by ID",
)
async def get_product_by_id(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> FinancialProduct:
    """
    Retrieve single financial product metadata by unique ID.
    """
    repo = FinancialProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial product with id {product_id} not found.",
        )
    return product


@router.get(
    "/financial-products/{product_id}/market-data",
    response_model=List[MarketDataResponse],
    summary="Get historical market price series for a product",
)
async def get_product_market_data(
    product_id: int,
    start_date: Optional[datetime] = Query(None, description="Filter from timestamp (ISO-8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter to timestamp (ISO-8601)"),
    limit: int = Query(500, ge=1, le=2000, description="Max historical price points"),
    db: AsyncSession = Depends(get_db),
) -> List[MarketData]:
    """
    Retrieve historical OHLCV market pricing series for a specific product.
    """
    repo = FinancialProductRepository(db)
    # Check product exists
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial product with id {product_id} not found.",
        )

    return await repo.get_market_data_for_product(
        product_id=product_id,
        start_time=start_date,
        end_time=end_date,
        limit=limit,
    )


@router.post(
    "/financial-products/ingest",
    response_model=IngestionSummary,
    summary="Ingest development financial products and market data",
)
async def ingest_development_data(
    db: AsyncSession = Depends(get_db),
) -> IngestionSummary:
    """
    Ingest pre-configured development sample CSV datasets (idempotent).
    """
    # Locate data directory relative to project root / backend
    possible_paths = [
        Path("../data"),
        Path("data"),
        Path("../../data"),
    ]

    base_data_dir = None
    for p in possible_paths:
        if (p / "financial_products.csv").exists():
            base_data_dir = p
            break

    if not base_data_dir:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not locate development data/ directory with financial_products.csv",
        )

    products_csv = base_data_dir / "financial_products.csv"
    market_csv = base_data_dir / "market_data.csv"

    service = IngestionService(db)
    return await service.ingest_from_csv(
        products_source=products_csv,
        market_data_source=market_csv if market_csv.exists() else None,
    )
