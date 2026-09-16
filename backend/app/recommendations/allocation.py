from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Sequence, Tuple, Union
from app.models.financial_goal import FinancialGoal
from app.recommendations.policy import (
    GoalHorizonBucket,
    GOAL_AWARE_ALLOCATION_MATRIX,
    RISK_GUARDRAILS,
    classify_horizon_bucket,
    generate_allocation_reasons,
    quantize_dec,
)
from app.recommendations.schemas import TargetAllocationSummary
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.enums import Priority

GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]


def determine_primary_horizon(goals: Sequence[GoalTypeUnion]) -> Tuple[Optional[Decimal], GoalHorizonBucket]:
    """
    Determines the representative time-horizon for portfolio formulation from goals.
    Respects priority hierarchy: High > Medium > Low.
    For tied priorities, selects the nearest deadline to protect against near-term sequence-of-returns risk.
    """
    if not goals:
        return None, GoalHorizonBucket.GENERAL_WEALTH

    # Filter goals with positive valid target_years
    valid_goals = [g for g in goals if getattr(g, "target_years", 0) and g.target_years > 0]
    if not valid_goals:
        return None, GoalHorizonBucket.GENERAL_WEALTH

    priority_map = {
        Priority.high: 3,
        "high": 3,
        Priority.medium: 2,
        "medium": 2,
        Priority.low: 1,
        "low": 1,
    }

    def goal_rank(g: GoalTypeUnion):
        p_val = priority_map.get(getattr(g, "priority", Priority.medium), 2)
        # Sort descending by priority rank, then ascending by target_years (nearest first)
        return (-p_val, g.target_years)

    sorted_goals = sorted(valid_goals, key=goal_rank)
    primary_goal = sorted_goals[0]
    horizon_dec = Decimal(str(primary_goal.target_years))
    bucket = classify_horizon_bucket(horizon_dec)
    return horizon_dec, bucket


def generate_target_allocation(
    risk_category: str,
    goals: Sequence[GoalTypeUnion] = (),
    target_years: Optional[Union[int, float, Decimal]] = None,
) -> TargetAllocationSummary:
    """
    Generates deterministic target asset allocation percentages based on user risk category
    and goal-horizon policy. Ensures sum(percentages) == 100.00% and satisfies risk guardrails.
    """
    alloc, _, _ = generate_goal_aware_allocation_with_reasons(
        risk_category=risk_category,
        goals=goals,
        target_years=target_years,
    )
    return alloc


def generate_goal_aware_allocation_with_reasons(
    risk_category: str,
    goals: Sequence[GoalTypeUnion] = (),
    target_years: Optional[Union[int, float, Decimal]] = None,
) -> Tuple[TargetAllocationSummary, Dict[str, str], GoalHorizonBucket]:
    """
    Generates deterministic target allocation percentages AND asset-class rationale strings,
    honoring risk profile ceilings, horizon rules, and exact 100.00% Decimal precision.
    """
    cat_key = risk_category.upper()
    if cat_key not in GOAL_AWARE_ALLOCATION_MATRIX:
        cat_key = "MODERATE"

    if target_years is not None:
        horizon_bucket = classify_horizon_bucket(target_years)
    else:
        _, horizon_bucket = determine_primary_horizon(goals)

    matrix_entry = GOAL_AWARE_ALLOCATION_MATRIX[cat_key].get(
        horizon_bucket,
        GOAL_AWARE_ALLOCATION_MATRIX[cat_key][GoalHorizonBucket.GENERAL_WEALTH],
    )

    equity = Decimal(str(matrix_entry["equity"]))
    debt = Decimal(str(matrix_entry["debt"]))
    gold = Decimal(str(matrix_entry["gold"]))
    cash = Decimal(str(matrix_entry["cash"]))

    # Apply hard risk guardrails (ceiling on high-volatility assets)
    guardrail = RISK_GUARDRAILS.get(cat_key)
    if guardrail:
        max_eq = guardrail.get("max_equity")
        if max_eq is not None and equity > max_eq:
            diff_eq = equity - max_eq
            equity = max_eq
            debt += diff_eq

        max_gld = guardrail.get("max_gold")
        if max_gld is not None and gold > max_gld:
            diff_gld = gold - max_gld
            gold = max_gld
            debt += diff_gld

    # Exact 100.00% normalization
    total = equity + debt + gold + cash
    if total != Decimal("100.00") and total > Decimal("0.00"):
        diff = Decimal("100.00") - total
        debt += diff

    equity_q = quantize_dec(equity, 2)
    debt_q = quantize_dec(debt, 2)
    gold_q = quantize_dec(gold, 2)
    cash_q = quantize_dec(cash, 2)

    # Double check quantized sum
    q_total = equity_q + debt_q + gold_q + cash_q
    if q_total != Decimal("100.00"):
        debt_q += Decimal("100.00") - q_total

    summary = TargetAllocationSummary(
        equity_pct=equity_q,
        debt_pct=debt_q,
        gold_pct=gold_q,
        cash_pct=cash_q,
    )

    reasons = generate_allocation_reasons(
        risk_category=cat_key,
        horizon_bucket=horizon_bucket,
        equity_pct=equity_q,
        debt_pct=debt_q,
        gold_pct=gold_q,
        cash_pct=cash_q,
    )

    return summary, reasons, horizon_bucket
