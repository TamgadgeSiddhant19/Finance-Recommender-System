from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.financial_data.models import FinancialProduct, MarketData
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductCreate,
    MarketDataCreate,
    ProductRiskLevel,
    ProductType,
)


class FinancialProductRepository:
    """
    Repository layer isolating all database interactions for financial products and market data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: int) -> Optional[FinancialProduct]:
        """Fetch a single financial product by primary key ID."""
        result = await self.db.execute(
            select(FinancialProduct).where(FinancialProduct.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_symbol(self, symbol: str) -> Optional[FinancialProduct]:
        """Fetch a single financial product by unique symbol/ticker."""
        clean_symbol = symbol.strip().upper()
        result = await self.db.execute(
            select(FinancialProduct).where(FinancialProduct.symbol == clean_symbol)
        )
        return result.scalar_one_or_none()

    async def create_product(self, product_in: FinancialProductCreate) -> FinancialProduct:
        """Create a new financial product record."""
        db_product = FinancialProduct(**product_in.model_dump())
        self.db.add(db_product)
        await self.db.commit()
        await self.db.refresh(db_product)
        return db_product

    async def upsert_product(self, product_in: FinancialProductCreate) -> Tuple[FinancialProduct, bool]:
        """
        Idempotently create or update a financial product by symbol.
        Returns a tuple of (FinancialProduct, is_created: bool).
        """
        existing = await self.get_by_symbol(product_in.symbol)
        if existing:
            # Update mutable fields
            for key, val in product_in.model_dump().items():
                setattr(existing, key, val)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False

        new_product = FinancialProduct(**product_in.model_dump())
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product, True

    async def list_products(self, skip: int = 0, limit: int = 100) -> List[FinancialProduct]:
        """List all financial products with pagination."""
        result = await self.db.execute(
            select(FinancialProduct).order_by(FinancialProduct.symbol.asc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def filter_products(
        self,
        asset_class: Optional[AssetClass] = None,
        product_type: Optional[ProductType] = None,
        risk_level: Optional[ProductRiskLevel] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FinancialProduct]:
        """Filter financial products by asset class, product type, or risk level."""
        query = select(FinancialProduct)
        if asset_class:
            query = query.where(FinancialProduct.asset_class == asset_class)
        if product_type:
            query = query.where(FinancialProduct.product_type == product_type)
        if risk_level:
            query = query.where(FinancialProduct.risk_level == risk_level)

        query = query.order_by(FinancialProduct.symbol.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def upsert_market_data(
        self,
        record_in: MarketDataCreate,
        product_id: int,
    ) -> Tuple[MarketData, bool]:
        """
        Idempotently insert or update a market OHLCV price record by (financial_product_id, timestamp).
        """
        result = await self.db.execute(
            select(MarketData).where(
                MarketData.financial_product_id == product_id,
                MarketData.timestamp == record_in.timestamp,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.open_price = record_in.open_price
            existing.high_price = record_in.high_price
            existing.low_price = record_in.low_price
            existing.close_price = record_in.close_price
            existing.volume = record_in.volume
            existing.source = record_in.source
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, False

        new_md = MarketData(
            financial_product_id=product_id,
            timestamp=record_in.timestamp,
            open_price=record_in.open_price,
            high_price=record_in.high_price,
            low_price=record_in.low_price,
            close_price=record_in.close_price,
            volume=record_in.volume,
            source=record_in.source,
        )
        self.db.add(new_md)
        await self.db.commit()
        await self.db.refresh(new_md)
        return new_md, True

    async def get_market_data_for_product(
        self,
        product_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[MarketData]:
        """Retrieve chronological historical market data series for a product."""
        query = select(MarketData).where(MarketData.financial_product_id == product_id)
        if start_time:
            query = query.where(MarketData.timestamp >= start_time)
        if end_time:
            query = query.where(MarketData.timestamp <= end_time)

        query = query.order_by(MarketData.timestamp.asc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
