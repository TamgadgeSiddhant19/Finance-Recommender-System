from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    risk_category: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_capacity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_equity_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_debt_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_gold_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_cash_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    total_monthly_sip: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_lump_sum: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Goal-Aware Allocation Extensions
    goal_horizon_bucket: Mapped[Optional[str]] = mapped_column(String(50), default="GENERAL_WEALTH", nullable=True)
    goal_feasibility_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    goal_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    items: Mapped[List["RecommendationItem"]] = relationship(
        "RecommendationItem",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="RecommendationItem.allocation_percentage.desc()",
    )


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    financial_product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("financial_products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    suitability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    allocation_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    monthly_sip_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    lump_sum_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    selection_reasons: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="items")
