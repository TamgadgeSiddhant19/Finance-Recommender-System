from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.schemas.enums import RiskTolerance, InvestmentExperience

if TYPE_CHECKING:
    from app.models.user import User


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_investment_capacity: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_debt: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    risk_tolerance: Mapped[RiskTolerance] = mapped_column(
        SAEnum(RiskTolerance, name="risk_tolerance_enum", native_enum=True),
        nullable=False,
    )
    investment_experience: Mapped[InvestmentExperience] = mapped_column(
        SAEnum(InvestmentExperience, name="investment_experience_enum", native_enum=True),
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
    user: Mapped["User"] = relationship("User", back_populates="financial_profile")
