"""
Deterministic Mathematical Engine for Financial Goal Feasibility & Projection.
Pure Python mathematical computations with exact Decimal precision.
Zero LLM involvement — completely reproducible, auditable, and unit-tested.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from app.goals.schemas import (
    CalculationAssumptions,
    GoalFeasibilityStatus,
    GoalProjectionResponse,
)
from app.schemas.enums import GoalType


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Rounds a Decimal to specified decimal places using ROUND_HALF_UP."""
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def get_default_expected_return(years: int) -> Decimal:
    """
    Standard conservative Indian market return assumptions based on investment horizon:
    - Short-Term (< 3 years): 6.5% p.a. (Fixed income / Liquid / Arbitrage)
    - Medium-Term (3–7 years): 9.5% p.a. (Hybrid / Conservative Balanced Advantage)
    - Long-Term (> 7 years): 11.5% p.a. (Diversified Broad Equity / Index)
    """
    if years < 3:
        return Decimal("0.065")
    elif years <= 7:
        return Decimal("0.095")
    else:
        return Decimal("0.115")


def calculate_future_value_lump_sum(
    pv: Decimal, annual_rate: Decimal, years: int
) -> Decimal:
    """
    Calculates Future Value (FV) of currently accumulated lump sum with monthly compounding:
    FV = PV * (1 + r_m)^(years * 12)
    """
    if pv <= Decimal("0.00") or years <= 0:
        return max(Decimal("0.00"), pv)

    if annual_rate <= Decimal("0.00"):
        return pv

    months = years * 12
    monthly_rate = annual_rate / Decimal("12.0")
    growth_multiplier = (Decimal("1.0") + monthly_rate) ** months
    return pv * growth_multiplier


def calculate_future_value_sip(
    monthly_amount: Decimal, annual_rate: Decimal, years: int
) -> Decimal:
    """
    Calculates Future Value (FV) of a periodic monthly SIP (Annuity Due / Beginning of Period):
    FV = PMT * [ ((1 + r_m)^n - 1) / r_m ] * (1 + r_m)
    """
    if monthly_amount <= Decimal("0.00") or years <= 0:
        return Decimal("0.00")

    months = years * 12

    if annual_rate <= Decimal("0.00"):
        return monthly_amount * Decimal(str(months))

    monthly_rate = annual_rate / Decimal("12.0")
    compound_multiplier = (Decimal("1.0") + monthly_rate) ** months
    annuity_factor = ((compound_multiplier - Decimal("1.0")) / monthly_rate) * (
        Decimal("1.0") + monthly_rate
    )
    return monthly_amount * annuity_factor


def calculate_inflation_adjusted_target(
    nominal_target: Decimal, inflation_rate: Decimal, years: int
) -> Decimal:
    """
    Adjusts nominal target amount for annual inflation compounding:
    Target_inflation = Target_nominal * (1 + i)^years
    """
    if nominal_target <= Decimal("0.00") or years <= 0:
        return max(Decimal("0.00"), nominal_target)

    if inflation_rate <= Decimal("0.00"):
        return nominal_target

    inflation_multiplier = (Decimal("1.0") + inflation_rate) ** years
    return nominal_target * inflation_multiplier


def calculate_required_sip(
    target_amount: Decimal,
    current_amount: Decimal,
    annual_rate: Decimal,
    years: int,
    inflation_rate: Decimal = Decimal("0.00"),
) -> Decimal:
    """
    Calculates exact monthly SIP contribution needed to bridge the gap to the inflation-adjusted target:
    PMT_req = Remaining_Corpus / Annuity_Factor(r_m, n)
    """
    if years <= 0:
        return Decimal("0.00")

    target_adj = calculate_inflation_adjusted_target(target_amount, inflation_rate, years)
    fv_current = calculate_future_value_lump_sum(current_amount, annual_rate, years)
    remaining_corpus = max(Decimal("0.00"), target_adj - fv_current)

    if remaining_corpus <= Decimal("0.00"):
        return Decimal("0.00")

    months = years * 12
    if annual_rate <= Decimal("0.00"):
        return remaining_corpus / Decimal(str(months))

    monthly_rate = annual_rate / Decimal("12.0")
    compound_multiplier = (Decimal("1.0") + monthly_rate) ** months
    annuity_factor = ((compound_multiplier - Decimal("1.0")) / monthly_rate) * (
        Decimal("1.0") + monthly_rate
    )
    return remaining_corpus / annuity_factor


def calculate_required_annual_return(
    target_amount: Decimal,
    current_amount: Decimal,
    monthly_amount: Decimal,
    years: int,
    inflation_rate: Decimal = Decimal("0.00"),
) -> Optional[Decimal]:
    """
    Determines the annual rate of return (%) required to reach the target with the given contribution.
    Uses deterministic bisection root-finding bounded in [0.00, 1.00] (up to 100% p.a.).
    Returns None if mathematically impossible even at 100% p.a.
    """
    if years <= 0:
        return None

    target_adj = calculate_inflation_adjusted_target(target_amount, inflation_rate, years)

    # 1. Check if already achievable at 0% return
    fv_at_zero = calculate_future_value_lump_sum(current_amount, Decimal("0.0"), years) + calculate_future_value_sip(
        monthly_amount, Decimal("0.0"), years
    )
    if fv_at_zero >= target_adj:
        return Decimal("0.00")

    # 2. Check upper bound at 100% annual return
    fv_at_max = calculate_future_value_lump_sum(current_amount, Decimal("1.00"), years) + calculate_future_value_sip(
        monthly_amount, Decimal("1.00"), years
    )
    if fv_at_max < target_adj:
        return None  # Unachievable within realistic market return parameters

    # 3. Bisection search for required rate
    low = Decimal("0.00")
    high = Decimal("1.00")
    tolerance = Decimal("0.0001")  # Precision to 0.01%

    for _ in range(50):
        mid = (low + high) / Decimal("2.0")
        fv_mid = calculate_future_value_lump_sum(current_amount, mid, years) + calculate_future_value_sip(
            monthly_amount, mid, years
        )

        if abs(fv_mid - target_adj) <= Decimal("10.00") or (high - low) <= tolerance:
            return quantize_dec(mid * Decimal("100.0"), 2)

        if fv_mid < target_adj:
            low = mid
        else:
            high = mid

    return quantize_dec(((low + high) / Decimal("2.0")) * Decimal("100.0"), 2)


def classify_goal_feasibility(
    projected_corpus: Decimal, inflation_adjusted_target: Decimal
) -> Tuple[GoalFeasibilityStatus, Decimal]:
    """
    Classifies goal feasibility based on Funding Ratio (Projected Corpus / Inflation Adjusted Target):
    - ON_TRACK: >= 100.0%
    - MODERATELY_UNDERFUNDED: 75.0% to 99.9%
    - SIGNIFICANTLY_UNDERFUNDED: 40.0% to 74.9%
    - NOT_FEASIBLE: < 40.0%
    """
    if inflation_adjusted_target <= Decimal("0.00"):
        return GoalFeasibilityStatus.ON_TRACK, Decimal("100.00")

    ratio = (projected_corpus / inflation_adjusted_target) * Decimal("100.00")
    ratio_rounded = quantize_dec(ratio, 2)

    if ratio_rounded >= Decimal("100.00"):
        return GoalFeasibilityStatus.ON_TRACK, ratio_rounded
    elif ratio_rounded >= Decimal("75.00"):
        return GoalFeasibilityStatus.MODERATELY_UNDERFUNDED, ratio_rounded
    elif ratio_rounded >= Decimal("40.00"):
        return GoalFeasibilityStatus.SIGNIFICANTLY_UNDERFUNDED, ratio_rounded
    else:
        return GoalFeasibilityStatus.NOT_FEASIBLE, ratio_rounded


def generate_feasibility_recommendations(
    status: GoalFeasibilityStatus,
    shortfall_or_surplus: Decimal,
    required_sip: Decimal,
    current_sip: Decimal,
    horizon_years: int,
    req_return_pct: Optional[Decimal],
) -> List[str]:
    """
    Generates actionable, deterministic financial guidance based on mathematical projection outputs.
    """
    recs: List[str] = []

    if status == GoalFeasibilityStatus.ON_TRACK:
        surplus_amt = quantize_dec(shortfall_or_surplus, 2)
        recs.append(
            f"Your current savings and SIP trajectory are on track with a projected surplus of ₹{surplus_amt:,.2f}."
        )
        recs.append(
            "Maintain current monthly investments and review asset allocation annually to stay ahead of inflation."
        )
    elif status == GoalFeasibilityStatus.MODERATELY_UNDERFUNDED:
        additional_sip = quantize_dec(max(Decimal("0.00"), required_sip - current_sip), 2)
        recs.append(
            f"Moderate funding gap detected. Increasing your monthly SIP by ₹{additional_sip:,.2f} will fully bridge the shortfall."
        )
        if horizon_years <= 5:
            recs.append(
                f"Alternatively, extending your goal timeline by 1 to 2 years would allow compounding to cover the target."
            )
        if req_return_pct and req_return_pct <= Decimal("15.00"):
            recs.append(
                f"Achieving the goal without additional SIP would require an annual portfolio return of {req_return_pct}%."
            )
    elif status == GoalFeasibilityStatus.SIGNIFICANTLY_UNDERFUNDED:
        additional_sip = quantize_dec(max(Decimal("0.00"), required_sip - current_sip), 2)
        recs.append(
            f"Significant shortfall of ₹{abs(shortfall_or_surplus):,.2f}. Required monthly contribution is ₹{required_sip:,.2f}/mo (an increase of ₹{additional_sip:,.2f}/mo)."
        )
        recs.append(
            "Consider stepping up your SIP by 10% annually with income growth, or re-evaluating the nominal target corpus."
        )
    else:  # NOT_FEASIBLE
        recs.append(
            f"Goal is currently underfunded relative to the {horizon_years}-year timeline. Current trajectory covers less than 40% of target."
        )
        recs.append(
            f"Required monthly contribution is ₹{required_sip:,.2f}/mo. We recommend extending your investment horizon or prioritizing core goals first."
        )

    return recs


def calculate_complete_goal_projection(
    target_amount: Decimal,
    current_amount: Decimal,
    horizon_years: int,
    monthly_contribution: Decimal = Decimal("0.00"),
    expected_annual_return: Optional[Decimal] = None,
    inflation_rate: Decimal = Decimal("0.06"),
    goal_id: Optional[int] = None,
    goal_type: GoalType = GoalType.retirement,
) -> GoalProjectionResponse:
    """
    High-level orchestrator computing the complete mathematical projection for a goal.
    """
    annual_rate = (
        expected_annual_return
        if expected_annual_return is not None
        else get_default_expected_return(horizon_years)
    )

    # 1. Growth calculations
    target_inflated = calculate_inflation_adjusted_target(
        nominal_target=target_amount,
        inflation_rate=inflation_rate,
        years=horizon_years,
    )
    fv_current = calculate_future_value_lump_sum(
        pv=current_amount,
        annual_rate=annual_rate,
        years=horizon_years,
    )
    fv_sip = calculate_future_value_sip(
        monthly_amount=monthly_contribution,
        annual_rate=annual_rate,
        years=horizon_years,
    )
    projected_corpus = fv_current + fv_sip
    shortfall_or_surplus = projected_corpus - target_inflated

    # 2. Feasibility Classification & Funding Ratio
    status, funding_ratio = classify_goal_feasibility(
        projected_corpus=projected_corpus,
        inflation_adjusted_target=target_inflated,
    )

    # 3. Required SIP & Required Return
    req_sip = calculate_required_sip(
        target_amount=target_amount,
        current_amount=current_amount,
        annual_rate=annual_rate,
        years=horizon_years,
        inflation_rate=inflation_rate,
    )
    req_return = calculate_required_annual_return(
        target_amount=target_amount,
        current_amount=current_amount,
        monthly_amount=monthly_contribution,
        years=horizon_years,
        inflation_rate=inflation_rate,
    )

    # 4. Actionable recommendations
    recs = generate_feasibility_recommendations(
        status=status,
        shortfall_or_surplus=shortfall_or_surplus,
        required_sip=req_sip,
        current_sip=monthly_contribution,
        horizon_years=horizon_years,
        req_return_pct=req_return,
    )

    return GoalProjectionResponse(
        goal_id=goal_id,
        goal_type=goal_type,
        target_amount=quantize_dec(target_amount, 2),
        current_amount=quantize_dec(current_amount, 2),
        monthly_contribution=quantize_dec(monthly_contribution, 2),
        horizon_years=horizon_years,
        expected_annual_return_pct=quantize_dec(annual_rate * Decimal("100.0"), 2),
        inflation_rate_pct=quantize_dec(inflation_rate * Decimal("100.0"), 2),
        inflation_adjusted_target=quantize_dec(target_inflated, 2),
        projected_current_growth=quantize_dec(fv_current, 2),
        projected_sip_growth=quantize_dec(fv_sip, 2),
        projected_corpus=quantize_dec(projected_corpus, 2),
        projected_shortfall_or_surplus=quantize_dec(shortfall_or_surplus, 2),
        funding_ratio_pct=funding_ratio,
        required_monthly_contribution=quantize_dec(req_sip, 2),
        required_annual_return_pct=req_return,
        feasibility_status=status,
        assumptions=CalculationAssumptions(),
        recommendations=recs,
    )
