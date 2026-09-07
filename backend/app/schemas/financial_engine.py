from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.enums import (
    GoalType,
    InvestmentExperience,
    Priority,
    RiskTolerance,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase


# ------------------------------------------------------------------------------
# 1. Financial Health Schemas
# ------------------------------------------------------------------------------
class FinancialHealthMetrics(BaseModel):
    monthly_surplus: Decimal = Field(..., description="Monthly income minus monthly expenses (INR)")
    emergency_fund_runway_months: Decimal = Field(..., description="Months of expenses covered by current savings")
    target_emergency_fund: Decimal = Field(..., description="Recommended emergency fund target (6 months of expenses, INR)")
    emergency_fund_status: str = Field(..., description="DEFICIENT (<3m), MODERATE (3-6m), HEALTHY (6-12m), SURPLUS (>12m)")
    emergency_fund_gap: Decimal = Field(..., description="Shortfall in emergency fund, 0 if adequate (INR)")
    debt_to_income_ratio: Decimal = Field(..., description="Total debt divided by annual income")
    surplus_to_income_ratio: Decimal = Field(..., description="Percentage of monthly income remaining as surplus")
    investment_capacity_ratio: Decimal = Field(..., description="Percentage of monthly income designated for investment")


# ------------------------------------------------------------------------------
# 2. Risk Assessment Schemas
# ------------------------------------------------------------------------------
class RiskAssessmentResult(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Composite deterministic risk score (0-100)")
    risk_category: str = Field(..., description="CONSERVATIVE, MODERATE, AGGRESSIVE, or VERY_AGGRESSIVE")
    stated_tolerance: RiskTolerance
    investment_experience: InvestmentExperience
    age: int
    score_breakdown: dict = Field(..., description="Factor breakdown explaining the composite score")


# ------------------------------------------------------------------------------
# 3. Asset Allocation Schemas
# ------------------------------------------------------------------------------
class AssetAllocationConstraint(BaseModel):
    equity_min_pct: Decimal = Field(..., description="Minimum recommended equity allocation percentage")
    equity_max_pct: Decimal = Field(..., description="Maximum recommended equity exposure percentage")
    debt_min_pct: Decimal = Field(..., description="Minimum recommended debt/fixed income percentage")
    debt_max_pct: Decimal = Field(..., description="Maximum recommended debt/fixed income percentage")
    gold_pct: Decimal = Field(..., description="Recommended gold/commodity exposure percentage")
    liquid_reserve_pct: Decimal = Field(..., description="Recommended liquid/cash reserve percentage")


class SIPAssetAllocation(BaseModel):
    asset_class: str = Field(..., description="Asset class name (e.g. Domestic Equity, Debt & Fixed Income, Gold)")
    allocation_pct: Decimal = Field(..., description="Percentage of total investment capacity")
    monthly_sip_amount: Decimal = Field(..., description="Calculated monthly SIP in INR")
    instrument_types: List[str] = Field(..., description="Representative Indian instruments for this asset class")


class AssetAllocationBreakdown(BaseModel):
    constraints: AssetAllocationConstraint
    recommended_sip_breakdown: List[SIPAssetAllocation]
    total_monthly_investment: Decimal = Field(..., description="Total monthly investment capacity in INR")
    recommended_emergency_buffer: Decimal = Field(..., description="Recommended liquid emergency reserve in INR")


# ------------------------------------------------------------------------------
# 4. Goal Analysis Schemas
# ------------------------------------------------------------------------------
class SingleGoalAnalysis(BaseModel):
    goal_id: Optional[int] = None
    goal_type: GoalType
    target_amount: Decimal
    current_amount: Decimal
    target_years: int
    priority: Priority
    horizon_category: str = Field(..., description="Short-Term (<3y), Medium-Term (3-7y), Long-Term (>7y)")
    expected_annual_return_pct: Decimal = Field(..., description="Assumed conservative real CAGR for this horizon")
    required_monthly_sip: Decimal = Field(..., description="Calculated required monthly SIP to achieve target in INR")
    projected_future_value_from_current: Decimal = Field(..., description="Compounded future value of current savings in INR")
    remaining_corpus_needed: Decimal = Field(..., description="Target minus future value of current amount in INR")


class GoalFeasibilityReport(BaseModel):
    individual_goals: List[SingleGoalAnalysis]
    total_required_monthly_sip: Decimal = Field(..., description="Total monthly investment required for all goals (INR)")
    user_investment_capacity: Decimal = Field(..., description="User's available monthly investment capacity (INR)")
    monthly_capacity_surplus_deficit: Decimal = Field(..., description="Available capacity minus total required SIP (INR)")
    is_fully_funded: bool = Field(..., description="True if capacity covers all required goal SIPs")
    funding_coverage_pct: Decimal = Field(..., description="Percentage of required SIP covered by capacity")
    recommendation_summary: str = Field(..., description="Deterministic guidance on goal prioritization")


# ------------------------------------------------------------------------------
# 5. Top-level Analysis Schemas
# ------------------------------------------------------------------------------
class ComprehensiveFinancialAnalysisResponse(BaseModel):
    user_id: Optional[int] = None
    currency: str = "INR"
    financial_health: FinancialHealthMetrics
    risk_assessment: RiskAssessmentResult
    asset_allocation: AssetAllocationBreakdown
    goal_analysis: GoalFeasibilityReport


class SimulationRequest(BaseModel):
    profile: FinancialProfileBase
    goals: List[FinancialGoalBase] = Field(default_factory=list)
