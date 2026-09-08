from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.financial_data.schemas import (
    AssetClass,
    FinancialProductResponse,
    ProductRiskLevel,
    ProductType,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase


class ProductSelectionReason(BaseModel):
    category: str = Field(..., description="Category of selection rationale (e.g., Risk Fit, Horizon, Cost Efficiency)")
    description: str = Field(..., description="Human-readable explanation of why this product was selected")
    score_contribution: Decimal = Field(..., description="Weighted score points contributed by this factor")


class RecommendedPortfolioItem(BaseModel):
    product_id: int = Field(..., description="Database ID of the financial product")
    symbol: str = Field(..., description="Instrument symbol or ticker")
    name: str = Field(..., description="Full descriptive name of the financial product")
    product_type: ProductType = Field(..., description="Classification category")
    asset_class: AssetClass = Field(..., description="Asset class allocation category")
    risk_level: ProductRiskLevel = Field(..., description="Assigned risk rating")
    suitability_score: Decimal = Field(..., ge=0, le=100, description="Overall suitability score (0-100)")
    allocation_percentage: Decimal = Field(..., ge=0, le=100, description="Target percentage weight in portfolio")
    suggested_monthly_sip: Decimal = Field(..., ge=0, description="Recommended monthly SIP amount in INR")
    suggested_lump_sum: Decimal = Field(..., ge=0, description="Recommended one-time investment amount in INR")
    selection_reasons: List[ProductSelectionReason] = Field(default_factory=list, description="Deterministic selection reasons")


class ValidationCheck(BaseModel):
    check_name: str = Field(..., description="Name of the validation constraint check")
    passed: bool = Field(..., description="True if constraint passed, False otherwise")
    details: str = Field(..., description="Explanation of test result or deviation")


class PortfolioValidationReport(BaseModel):
    is_valid: bool = Field(..., description="Overall portfolio validity flag")
    checks: List[ValidationCheck] = Field(default_factory=list, description="Individual constraint evaluations")
    error_messages: List[str] = Field(default_factory=list, description="Blocking validation error messages")
    warning_messages: List[str] = Field(default_factory=list, description="Non-blocking optimization notices")


class TargetAllocationSummary(BaseModel):
    equity_pct: Decimal = Field(..., description="Target equity allocation percentage")
    debt_pct: Decimal = Field(..., description="Target debt allocation percentage")
    gold_pct: Decimal = Field(..., description="Target gold allocation percentage")
    cash_pct: Decimal = Field(..., description="Target cash/liquid allocation percentage")


class RecommendationResponse(BaseModel):
    recommendation_id: Optional[int] = Field(default=None, description="Database ID of stored recommendation if persisted")
    user_id: Optional[int] = Field(default=None, description="User ID for which recommendation was generated")
    risk_category: str = Field(..., description="Evaluated risk profile (CONSERVATIVE, MODERATE, AGGRESSIVE, VERY_AGGRESSIVE)")
    risk_score: int = Field(..., description="Deterministic multi-factor risk score (0-100)")
    monthly_investment_capacity: Decimal = Field(..., description="Available monthly surplus capacity in INR")
    target_allocation: TargetAllocationSummary = Field(..., description="Target asset class distribution")
    portfolio_items: List[RecommendedPortfolioItem] = Field(default_factory=list, description="Selected asset instruments")
    total_monthly_sip: Decimal = Field(..., description="Total monthly SIP sum in INR")
    total_lump_sum: Decimal = Field(..., description="Total lump sum allocation sum in INR")
    validation_report: PortfolioValidationReport = Field(..., description="Portfolio constraint verification results")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of generation")

    model_config = ConfigDict(from_attributes=True)



class RecommendationSimulateRequest(BaseModel):
    profile: FinancialProfileBase = Field(..., description="Financial profile data for stateless calculation")
    goals: List[FinancialGoalBase] = Field(default_factory=list, description="Active financial goals")
    available_products: Optional[List[FinancialProductResponse]] = Field(
        default=None,
        description="Optional list of financial products to evaluate against (defaults to DB catalog)",
    )


class RecommendationHistoryItem(BaseModel):
    id: int
    user_id: int
    risk_category: str
    risk_score: int
    monthly_capacity: Decimal
    target_equity_pct: Decimal
    target_debt_pct: Decimal
    target_gold_pct: Decimal
    target_cash_pct: Decimal
    is_valid: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
