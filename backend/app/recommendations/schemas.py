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
    category: str = Field(..., description="Category of selection rationale (e.g., Risk Fit, Horizon, Cost Efficiency, Market Intelligence)")
    description: str = Field(..., description="Human-readable explanation of why this product was selected")
    score_contribution: Decimal = Field(..., description="Weighted score points contributed by this factor")


class ProductExclusionSummary(BaseModel):
    product_id: Optional[int] = Field(default=None, description="Database ID of excluded product")
    symbol: str = Field(..., description="Instrument symbol")
    name: str = Field(..., description="Product name")
    asset_class: Optional[str] = Field(default=None, description="Asset class")
    risk_level: Optional[str] = Field(default=None, description="Risk level")
    reason: str = Field(..., description="Deterministic reason for exclusion")
    category: str = Field(default="Eligibility Filter", description="Exclusion classification category")


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

    # Phase 7.3 Product Intelligence & Risk-Adjusted Market Features
    risk_compatibility_score: Optional[Decimal] = Field(default=None, description="Risk alignment sub-score (0-100)")
    goal_compatibility_score: Optional[Decimal] = Field(default=None, description="Goal objective alignment sub-score (0-100)")
    horizon_compatibility_score: Optional[Decimal] = Field(default=None, description="Time-horizon alignment sub-score (0-100)")
    historical_return_1y: Optional[Decimal] = Field(default=None, description="1-year historical percentage return (Historical, not expected future return)")
    historical_return_3y: Optional[Decimal] = Field(default=None, description="3-year historical percentage return")
    historical_return_5y: Optional[Decimal] = Field(default=None, description="5-year historical percentage return")
    volatility: Optional[Decimal] = Field(default=None, description="Annualized historical volatility (%)")
    max_drawdown: Optional[Decimal] = Field(default=None, description="Maximum historical peak-to-trough decline (%)")
    current_drawdown: Optional[Decimal] = Field(default=None, description="Current drawdown percentage from peak (%)")
    expense_ratio: Optional[Decimal] = Field(default=None, description="Total Expense Ratio (TER)")
    data_quality_score: Optional[Decimal] = Field(default=None, description="Data verification quality score (0-100)")
    data_source: Optional[str] = Field(default="master_catalog", description="Source provider: alphavantage, upstox, demo, master_catalog")
    data_status: Optional[str] = Field(default="unavailable", description="Data status: historical, live, synthetic, unavailable")
    data_as_of: Optional[datetime] = Field(default=None, description="Timestamp of latest observation candle")


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


class GoalRecommendationSummary(BaseModel):
    goal_id: Optional[int] = Field(default=None, description="Database ID of goal if persisted")
    goal_type: str = Field(..., description="Goal classification type")
    target_amount: Decimal = Field(..., description="Nominal target amount in INR")
    current_amount: Decimal = Field(..., description="Currently accumulated savings in INR")
    target_years: int = Field(..., description="Investment horizon in years")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    feasibility_status: str = Field(..., description="Feasibility status (ON_TRACK, MODERATELY_UNDERFUNDED, SIGNIFICANTLY_UNDERFUNDED, NOT_FEASIBLE)")
    funding_ratio_pct: Decimal = Field(..., description="Percentage of inflation-adjusted target covered")
    projected_corpus: Decimal = Field(..., description="Estimated future value of savings and SIP in INR")
    inflation_adjusted_target: Decimal = Field(..., description="Inflation-adjusted corpus target in INR")
    shortfall_or_surplus: Decimal = Field(..., description="Surplus (+) or Shortfall (-) in INR")
    allocated_monthly_sip: Decimal = Field(..., description="Portion of monthly capacity allocated to this goal in INR")
    required_monthly_sip: Decimal = Field(..., description="SIP required to fully reach target in INR")
    horizon_bucket: str = Field(..., description="Horizon bucket: SHORT_TERM, MEDIUM_TERM, LONG_TERM")
    funding_gap_actions: List[str] = Field(default_factory=list, description="Deterministic actionable steps")


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

    # Phase 7.2 Goal-Aware Allocation Extensions
    goal_horizon_bucket: Optional[str] = Field(default="GENERAL_WEALTH", description="Primary goal horizon bucket (SHORT_TERM, MEDIUM_TERM, LONG_TERM, GENERAL_WEALTH)")
    goal_feasibility_status: Optional[str] = Field(default=None, description="Primary goal feasibility classification")
    nominal_target: Optional[Decimal] = Field(default=None, description="Nominal target amount of primary/aggregate goal in INR")
    inflation_adjusted_target: Optional[Decimal] = Field(default=None, description="Inflation-adjusted target amount in INR")
    projected_corpus: Optional[Decimal] = Field(default=None, description="Total projected corpus across current savings + SIP in INR")
    funding_ratio: Optional[Decimal] = Field(default=None, description="Funding ratio percentage")
    goal_shortfall_or_surplus: Optional[Decimal] = Field(default=None, description="Surplus (+) or Shortfall (-) relative to inflation-adjusted target in INR")
    goal_aware_allocation: Optional[TargetAllocationSummary] = Field(default=None, description="Goal-aware tactical asset allocation breakdown")
    allocation_reasons: Optional[Dict[str, str]] = Field(default=None, description="Deterministic per-asset-class rationale statements")
    funding_gap_actions: Optional[List[str]] = Field(default_factory=list, description="Deterministic actionable steps for funding optimization")
    goals_breakdown: Optional[List[GoalRecommendationSummary]] = Field(default_factory=list, description="Individual goal projections and priority allocation breakdown")

    # Phase 7.3 Product Intelligence & Exclusion Explanations
    excluded_products: List[ProductExclusionSummary] = Field(default_factory=list, description="Transparent exclusion audit trail")

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
    goal_horizon_bucket: Optional[str] = None
    goal_feasibility_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
