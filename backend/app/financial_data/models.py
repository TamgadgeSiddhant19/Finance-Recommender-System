from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.financial_data.schemas import (
    AssetClass,
    ProductRiskLevel,
    ProductType,
)


class FinancialProduct(Base):
    __tablename__ = "financial_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[ProductType] = mapped_column(
        SAEnum(ProductType, name="product_type_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    asset_class: Mapped[AssetClass] = mapped_column(
        SAEnum(AssetClass, name="asset_class_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="India", nullable=False)
    risk_level: Mapped[ProductRiskLevel] = mapped_column(
        SAEnum(ProductRiskLevel, name="product_risk_level_enum", native_enum=True),
        nullable=False,
        index=True,
    )
    expense_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    minimum_investment: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        default=Decimal("500.00"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    market_data: Mapped[List["MarketData"]] = relationship(
        "MarketData",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="MarketData.timestamp.asc()",
    )


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    financial_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("financial_products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="demo/synthetic", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    product: Mapped["FinancialProduct"] = relationship("FinancialProduct", back_populates="market_data")

    # Composite Unique Constraint and Indexes
    __table_args__ = (
        UniqueConstraint("financial_product_id", "timestamp", name="uq_market_data_product_timestamp"),
        Index("ix_market_data_product_timestamp", "financial_product_id", "timestamp"),
    )
