from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Sequence, Union
from app.models.financial_goal import FinancialGoal
from app.recommendations.constants import BASE_ALLOCATION_MATRIX
from app.recommendations.schemas import TargetAllocationSummary
from app.schemas.financial_goal import FinancialGoalBase

GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def generate_target_allocation(
    risk_category: str,
    goals: Sequence[GoalTypeUnion] = (),
) -> TargetAllocationSummary:
    """
    Generates deterministic target asset allocation percentages based on user risk category
    and time-horizon constraints. Ensures sum(percentages) == 100.00%.
    """
    cat_key = risk_category.upper()
    base = BASE_ALLOCATION_MATRIX.get(cat_key, BASE_ALLOCATION_MATRIX["MODERATE"])

    equity = Decimal(str(base["equity"]))
    debt = Decimal(str(base["debt"]))
    gold = Decimal(str(base["gold"]))
    cash = Decimal(str(base["cash"]))

    # Horizon-based tactical adjustment:
    # If the user has urgent goals with short average horizon (< 3 years),
    # mitigate equity sequence-of-returns risk by shifting equity to debt/cash.
    if goals:
        horizons = [Decimal(str(g.target_years)) for g in goals if g.target_years and g.target_years > 0]
        if horizons:
            avg_horizon = sum(horizons) / Decimal(len(horizons))
            if avg_horizon < Decimal("3.0"):
                # If short horizon, cap equity at 25% max
                if equity > Decimal("25.00"):
                    excess = equity - Decimal("25.00")
                    equity = Decimal("25.00")
                    debt += quantize_dec(excess * Decimal("0.70"), 2)
                    cash += quantize_dec(excess * Decimal("0.30"), 2)

    # Normalize to ensure exactly 100.00%
    total = equity + debt + gold + cash
    if total != Decimal("100.00") and total > Decimal("0.00"):
        diff = Decimal("100.00") - total
        # Adjust debt as balancer
        debt += diff

    return TargetAllocationSummary(
        equity_pct=quantize_dec(equity, 2),
        debt_pct=quantize_dec(debt, 2),
        gold_pct=quantize_dec(gold, 2),
        cash_pct=quantize_dec(cash, 2),
    )
