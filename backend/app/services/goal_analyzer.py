from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Sequence, Union
from app.schemas.financial_engine import (
    GoalFeasibilityReport,
    SingleGoalAnalysis,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.models.financial_goal import FinancialGoal


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def analyze_single_goal(
    goal: Union[FinancialGoalBase, FinancialGoal],
    goal_id: Optional[int] = None,
) -> SingleGoalAnalysis:
    """
    Perform deterministic compounding analysis on an individual financial goal:
    - Horizon classification and conservative Indian market return assumptions
    - Compounding of current savings
    - Exact monthly SIP requirement formula (annuity due)
    """
    target_amount = goal.target_amount
    current_amount = goal.current_amount
    years = goal.target_years
    months = years * 12

    # 1. Horizon Classification & Conservative Indian Expected Returns
    if years < 3:
        horizon_category = "Short-Term (<3 years)"
        annual_rate = Decimal("0.065")  # 6.5% p.a.
        rate_pct = Decimal("6.50")
    elif years <= 7:
        horizon_category = "Medium-Term (3-7 years)"
        annual_rate = Decimal("0.095")  # 9.5% p.a.
        rate_pct = Decimal("9.50")
    else:
        horizon_category = "Long-Term (>7 years)"
        annual_rate = Decimal("0.115")  # 11.5% p.a.
        rate_pct = Decimal("11.50")

    monthly_rate = annual_rate / Decimal("12.0")

    # 2. Future value of currently accumulated amount
    # FV_current = PV * (1 + r)^n
    compound_multiplier = (Decimal("1.0") + monthly_rate) ** months
    fv_current = current_amount * compound_multiplier

    remaining_corpus = max(Decimal("0.00"), target_amount - fv_current)

    # 3. Required Monthly SIP calculation (Annuity Due)
    # PMT = Remaining_Corpus / [ ((1 + r)^n - 1) / r * (1 + r) ]
    if remaining_corpus > Decimal("0.00") and months > 0:
        annuity_factor = ((compound_multiplier - Decimal("1.0")) / monthly_rate) * (Decimal("1.0") + monthly_rate)
        required_monthly_sip = remaining_corpus / annuity_factor
    else:
        required_monthly_sip = Decimal("0.00")

    actual_goal_id = getattr(goal, "id", goal_id)

    return SingleGoalAnalysis(
        goal_id=actual_goal_id,
        goal_type=goal.goal_type,
        target_amount=quantize_dec(target_amount, 2),
        current_amount=quantize_dec(current_amount, 2),
        target_years=years,
        priority=goal.priority,
        horizon_category=horizon_category,
        expected_annual_return_pct=rate_pct,
        required_monthly_sip=quantize_dec(required_monthly_sip, 2),
        projected_future_value_from_current=quantize_dec(fv_current, 2),
        remaining_corpus_needed=quantize_dec(remaining_corpus, 2),
    )


def calculate_goal_feasibility(
    goals: Sequence[Union[FinancialGoalBase, FinancialGoal]],
    user_investment_capacity: Decimal,
) -> GoalFeasibilityReport:
    """
    Assess collective feasibility of all user goals against available monthly investment capacity.
    """
    if not goals:
        return GoalFeasibilityReport(
            individual_goals=[],
            total_required_monthly_sip=Decimal("0.00"),
            user_investment_capacity=quantize_dec(user_investment_capacity, 2),
            monthly_capacity_surplus_deficit=quantize_dec(user_investment_capacity, 2),
            is_fully_funded=True,
            funding_coverage_pct=Decimal("100.00"),
            recommendation_summary="No active goals configured. Ready to allocate investment capacity to new goals.",
        )

    analyzed_goals: List[SingleGoalAnalysis] = []
    total_required_sip = Decimal("0.00")

    for g in goals:
        single_res = analyze_single_goal(g)
        analyzed_goals.append(single_res)
        total_required_sip += single_res.required_monthly_sip

    capacity_surplus_deficit = user_investment_capacity - total_required_sip
    is_funded = capacity_surplus_deficit >= Decimal("0.00")

    if total_required_sip > Decimal("0.00"):
        coverage_pct = (user_investment_capacity / total_required_sip) * Decimal("100.00")
    else:
        coverage_pct = Decimal("100.00")

    # Generate deterministic guidance summary
    if is_funded:
        surplus_amt = quantize_dec(capacity_surplus_deficit, 2)
        summary = (
            f"All financial goals are 100% achievable within your current capacity. "
            f"You have an unallocated monthly surplus of ₹{surplus_amt:,.2f} that can accelerate retirement or wealth creation."
        )
    else:
        deficit_amt = quantize_dec(abs(capacity_surplus_deficit), 2)
        summary = (
            f"Capacity shortfall of ₹{deficit_amt:,.2f}/month. Current investment capacity covers "
            f"{quantize_dec(coverage_pct, 1)}% of required goal contributions. Prioritize High-priority and "
            f"Emergency/Retirement goals first, or consider extending target horizons for discretionary goals."
        )

    return GoalFeasibilityReport(
        individual_goals=analyzed_goals,
        total_required_monthly_sip=quantize_dec(total_required_sip, 2),
        user_investment_capacity=quantize_dec(user_investment_capacity, 2),
        monthly_capacity_surplus_deficit=quantize_dec(capacity_surplus_deficit, 2),
        is_fully_funded=is_funded,
        funding_coverage_pct=quantize_dec(coverage_pct, 1),
        recommendation_summary=summary,
    )
