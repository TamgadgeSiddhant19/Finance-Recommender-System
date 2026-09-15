"""
Goal Feasibility & Projection Engine Schemas.
Enforces high-precision Decimal types and comprehensive projection metadata.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.enums import GoalType, Priority


class GoalFeasibilityStatus(str, Enum):
    """Feasibility classification of a financial goal based on funding ratio."""

    ON_TRACK = "ON_TRACK"
    MODERATELY_UNDERFUNDED = "MODERATELY_UNDERFUNDED"
    SIGNIFICANTLY_UNDERFUNDED = "SIGNIFICANTLY_UNDERFUNDED"
    NOT_FEASIBLE = "NOT_FEASIBLE"


class CalculationAssumptions(BaseModel):
    """Transparent assumptions underlying the deterministic projection."""

    compounding_frequency: str = Field(
        default="Monthly",
        description="Frequency of interest compounding for monthly contributions",
    )
    sip_timing: str = Field(
        default="Beginning of Month (Annuity Due)",
        description="Timing of monthly SIP investments",
    )
    inflation_model: str = Field(
        default="Annual compounding on target corpus",
        description="Inflation indexation methodology",
    )
    disclaimer: str = Field(
        default=(
            "Expected returns and inflation rates are assumptions used for mathematical modeling "
            "and do not constitute guaranteed returns or predictive forecasts."
        ),
        description="Regulatory financial disclaimer",
    )

    model_config = ConfigDict(from_attributes=True)


class GoalProjectionRequest(BaseModel):
    """Optional override parameters when computing a projection for an existing stored goal."""

    expected_annual_return: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=Decimal("0.50"),
        description="Custom expected annual return rate as a decimal (e.g. 0.12 for 12%). Defaults to horizon-based standard rate.",
    )
    inflation_rate: Optional[Decimal] = Field(
        default=Decimal("0.06"),
        ge=0,
        le=Decimal("0.30"),
        description="Assumed annual inflation rate (default 0.06 for 6.0% p.a. Indian CPI standard).",
    )
    monthly_contribution: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Optional custom monthly contribution override in INR. Defaults to user's allocated capacity.",
    )

    model_config = ConfigDict(from_attributes=True)


class GoalProjectionSimulateRequest(BaseModel):
    """Inputs for stateless goal feasibility simulation without saving to database."""

    goal_type: GoalType = Field(default=GoalType.retirement, description="Classification of the goal")
    target_amount: Decimal = Field(..., gt=0, description="Target financial goal amount in INR")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Currently accumulated amount in INR")
    target_years: int = Field(..., gt=0, le=100, description="Investment horizon in years")
    monthly_contribution: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Allocated or planned monthly contribution (SIP) in INR",
    )
    expected_annual_return: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=Decimal("0.50"),
        description="Expected annual return rate as a decimal (e.g. 0.10 for 10%). Defaults to horizon-based conservative Indian market rate.",
    )
    inflation_rate: Decimal = Field(
        default=Decimal("0.06"),
        ge=0,
        le=Decimal("0.30"),
        description="Assumed annual inflation rate (default 0.06 for 6.0% p.a.).",
    )
    priority: Priority = Field(default=Priority.medium, description="Priority rank of the goal")

    @field_validator("goal_type", mode="before")
    @classmethod
    def normalize_goal_type(cls, v):
        if isinstance(v, str):
            v_clean = v.lower().strip()
            if v_clean in ("house_downpayment", "house_purchase", "real_estate", "home"):
                return "house"
            return v_clean
        return v

    model_config = ConfigDict(from_attributes=True)


class GoalProjectionResponse(BaseModel):
    """
    Complete deterministic goal feasibility and projection report.
    """

    goal_id: Optional[int] = Field(default=None, description="Database ID of the goal if persisted")
    goal_type: GoalType = Field(..., description="Goal classification")
    target_amount: Decimal = Field(..., description="Nominal target amount in INR")
    current_amount: Decimal = Field(..., description="Currently accumulated amount in INR")
    monthly_contribution: Decimal = Field(..., description="Current/planned monthly contribution in INR")
    horizon_years: int = Field(..., description="Investment horizon in years")
    expected_annual_return_pct: Decimal = Field(..., description="Assumed annual return rate in %")
    inflation_rate_pct: Decimal = Field(..., description="Assumed annual inflation rate in %")
    
    # Growth Projections
    inflation_adjusted_target: Decimal = Field(..., description="Target corpus adjusted for inflation over the horizon in INR")
    projected_current_growth: Decimal = Field(..., description="Projected future value of current savings in INR")
    projected_sip_growth: Decimal = Field(..., description="Projected future value of monthly contributions in INR")
    projected_corpus: Decimal = Field(..., description="Total projected corpus (current savings growth + SIP growth) in INR")
    
    # Feasibility Metrics
    projected_shortfall_or_surplus: Decimal = Field(..., description="Surplus (+) or Shortfall (-) relative to inflation-adjusted target in INR")
    funding_ratio_pct: Decimal = Field(..., description="Percentage of inflation-adjusted target covered by projected corpus")
    required_monthly_contribution: Decimal = Field(..., description="Monthly contribution required to bridge the shortfall in INR")
    required_annual_return_pct: Optional[Decimal] = Field(
        default=None,
        description="Annual return rate (%) required to reach target with current contribution, or None if impossible",
    )
    feasibility_status: GoalFeasibilityStatus = Field(..., description="Feasibility classification category")
    
    # Transparency & Guidance
    assumptions: CalculationAssumptions = Field(
        default_factory=CalculationAssumptions,
        description="Underlying calculation parameters and disclaimers",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Deterministic, explainable guidance to achieve or optimize the goal",
    )

    model_config = ConfigDict(from_attributes=True)
