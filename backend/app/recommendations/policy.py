"""
Centralized Goal-Aware Asset Allocation Policy & Horizon Configuration.
Pure deterministic mathematical rules and templates. Zero LLM involvement.
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Tuple


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Rounds a Decimal to specified decimal places using ROUND_HALF_UP."""
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


class GoalHorizonBucket(str, Enum):
    """Configurable investment time-horizon buckets."""

    SHORT_TERM = "SHORT_TERM"      # < 3 years: Capital preservation & liquidity focus
    MEDIUM_TERM = "MEDIUM_TERM"    # 3–5 years: Balanced growth & volatility dampening
    LONG_TERM = "LONG_TERM"        # > 5 years: Long-term wealth creation & inflation beating
    GENERAL_WEALTH = "GENERAL_WEALTH"  # Fallback when no active goals exist


def classify_horizon_bucket(target_years: Optional[int | float | Decimal]) -> GoalHorizonBucket:
    """
    Classifies investment horizon into policy buckets:
    - < 3 years -> SHORT_TERM
    - 3 to 5 years (inclusive) -> MEDIUM_TERM
    - > 5 years -> LONG_TERM
    """
    if target_years is None:
        return GoalHorizonBucket.GENERAL_WEALTH

    years_val = float(target_years)
    if years_val < 3.0:
        return GoalHorizonBucket.SHORT_TERM
    elif years_val <= 5.0:
        return GoalHorizonBucket.MEDIUM_TERM
    else:
        return GoalHorizonBucket.LONG_TERM


# ------------------------------------------------------------------------------
# 1. Risk Profile Guardrails (Absolute Ceilings and Floors)
# ------------------------------------------------------------------------------
# Ensures goal horizon adjustments NEVER override the user's hard risk constraints.
RISK_GUARDRAILS: Dict[str, Dict[str, Decimal]] = {
    "CONSERVATIVE": {
        "max_equity": Decimal("30.00"),
        "min_debt": Decimal("50.00"),
        "max_gold": Decimal("15.00"),
        "min_cash": Decimal("0.00"),
    },
    "MODERATE": {
        "max_equity": Decimal("60.00"),
        "min_debt": Decimal("25.00"),
        "max_gold": Decimal("15.00"),
        "min_cash": Decimal("0.00"),
    },
    "AGGRESSIVE": {
        "max_equity": Decimal("80.00"),
        "min_debt": Decimal("10.00"),
        "max_gold": Decimal("15.00"),
        "min_cash": Decimal("0.00"),
    },
    "VERY_AGGRESSIVE": {
        "max_equity": Decimal("90.00"),
        "min_debt": Decimal("5.00"),
        "max_gold": Decimal("10.00"),
        "min_cash": Decimal("0.00"),
    },
}


# ------------------------------------------------------------------------------
# 2. Goal-Aware Allocation Matrix [Risk Profile][Horizon Bucket]
# ------------------------------------------------------------------------------
# Target percentages for Equity, Debt, Gold, Cash/Liquid.
# Sum per bucket == 100.00%.
GOAL_AWARE_ALLOCATION_MATRIX: Dict[str, Dict[GoalHorizonBucket, Dict[str, Decimal]]] = {
    "CONSERVATIVE": {
        GoalHorizonBucket.SHORT_TERM: {
            "equity": Decimal("10.00"),
            "debt": Decimal("70.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("15.00"),
        },
        GoalHorizonBucket.MEDIUM_TERM: {
            "equity": Decimal("20.00"),
            "debt": Decimal("65.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("5.00"),
        },
        GoalHorizonBucket.LONG_TERM: {
            "equity": Decimal("30.00"),
            "debt": Decimal("60.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.GENERAL_WEALTH: {
            "equity": Decimal("25.00"),
            "debt": Decimal("65.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("5.00"),
        },
    },
    "MODERATE": {
        GoalHorizonBucket.SHORT_TERM: {
            "equity": Decimal("15.00"),
            "debt": Decimal("65.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("15.00"),
        },
        GoalHorizonBucket.MEDIUM_TERM: {
            "equity": Decimal("45.00"),
            "debt": Decimal("45.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.LONG_TERM: {
            "equity": Decimal("55.00"),
            "debt": Decimal("35.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.GENERAL_WEALTH: {
            "equity": Decimal("55.00"),
            "debt": Decimal("35.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
    },
    "AGGRESSIVE": {
        GoalHorizonBucket.SHORT_TERM: {
            "equity": Decimal("20.00"),
            "debt": Decimal("60.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("15.00"),
        },
        GoalHorizonBucket.MEDIUM_TERM: {
            "equity": Decimal("60.00"),
            "debt": Decimal("30.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.LONG_TERM: {
            "equity": Decimal("75.00"),
            "debt": Decimal("15.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.GENERAL_WEALTH: {
            "equity": Decimal("75.00"),
            "debt": Decimal("15.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
    },
    "VERY_AGGRESSIVE": {
        GoalHorizonBucket.SHORT_TERM: {
            "equity": Decimal("25.00"),
            "debt": Decimal("55.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("15.00"),
        },
        GoalHorizonBucket.MEDIUM_TERM: {
            "equity": Decimal("70.00"),
            "debt": Decimal("20.00"),
            "gold": Decimal("10.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.LONG_TERM: {
            "equity": Decimal("85.00"),
            "debt": Decimal("10.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("0.00"),
        },
        GoalHorizonBucket.GENERAL_WEALTH: {
            "equity": Decimal("85.00"),
            "debt": Decimal("10.00"),
            "gold": Decimal("5.00"),
            "cash": Decimal("0.00"),
        },
    },
}


# ------------------------------------------------------------------------------
# 3. Deterministic Allocation Explanation Template Generator
# ------------------------------------------------------------------------------
def generate_allocation_reasons(
    risk_category: str,
    horizon_bucket: GoalHorizonBucket,
    equity_pct: Decimal,
    debt_pct: Decimal,
    gold_pct: Decimal,
    cash_pct: Decimal,
) -> Dict[str, str]:
    """
    Generates transparent, deterministic rationale statements for each asset class weight.
    Zero LLM involvement — purely template and rule-based.
    """
    cat = risk_category.upper()
    reasons: Dict[str, str] = {}

    # Equity Reason
    if horizon_bucket == GoalHorizonBucket.SHORT_TERM:
        reasons["equity"] = (
            f"Equity is capped at {equity_pct}% to protect capital against sequence-of-returns volatility "
            f"for short-term horizon (< 3 years)."
        )
    elif horizon_bucket == GoalHorizonBucket.MEDIUM_TERM:
        reasons["equity"] = (
            f"Equity allocation of {equity_pct}% provides moderate capital growth while respecting "
            f"{cat} risk profile guardrails for a 3–5 year timeline."
        )
    elif horizon_bucket == GoalHorizonBucket.LONG_TERM:
        reasons["equity"] = (
            f"Long-term horizon (> 5 years) allows growth-oriented {equity_pct}% equity exposure "
            f"to beat inflation while staying within {cat} risk guardrails."
        )
    else:
        reasons["equity"] = (
            f"Standard {equity_pct}% equity exposure optimized for long-term compound growth under "
            f"{cat} risk profile."
        )

    # Debt Reason
    if horizon_bucket == GoalHorizonBucket.SHORT_TERM:
        reasons["debt"] = (
            f"High debt allocation of {debt_pct}% provides principal preservation and predictable yields "
            f"as the goal deadline approaches."
        )
    elif horizon_bucket == GoalHorizonBucket.MEDIUM_TERM:
        reasons["debt"] = (
            f"Debt allocation of {debt_pct}% balances portfolio volatility and anchors overall stability."
        )
    else:
        reasons["debt"] = (
            f"Debt allocation of {debt_pct}% provides downside protection and liquidity rebalancing support."
        )

    # Gold Reason
    if gold_pct > Decimal("0.00"):
        reasons["gold"] = (
            f"Gold allocation of {gold_pct}% serves as an inflation hedge and provides non-correlated asset diversification."
        )
    else:
        reasons["gold"] = "No gold allocation allocated for this profile/horizon combination."

    # Cash Reason
    if cash_pct > Decimal("0.00"):
        reasons["cash"] = (
            f"Cash/Liquid allocation of {cash_pct}% ensures immediate liquidity and minimizes drawdown risk for near-term capital needs."
        )
    else:
        reasons["cash"] = "Zero cash drag maintained to maximize compounding in active yield-bearing assets."

    return reasons


# ------------------------------------------------------------------------------
# 4. Deterministic Funding Gap Action Generator
# ------------------------------------------------------------------------------
def generate_funding_gap_actions(
    feasibility_status: str,
    required_sip: Decimal,
    current_sip: Decimal,
    shortfall: Decimal,
    horizon_years: int,
) -> List[str]:
    """
    Generates deterministic, non-risking actionable steps when a goal is underfunded.
    CRITICAL RULE: Never recommends higher risk to close funding gaps.
    """
    status_upper = feasibility_status.upper()
    actions: List[str] = []

    if status_upper == "ON_TRACK":
        actions.append("Continue current monthly SIP allocation without altering portfolio risk.")
        actions.append("Review goal progress and inflation assumptions semi-annually.")

    elif status_upper == "MODERATELY_UNDERFUNDED":
        gap = max(Decimal("0.00"), required_sip - current_sip)
        actions.append(
            f"Increase monthly SIP by ₹{gap:,.2f} (from ₹{current_sip:,.2f} to ₹{required_sip:,.2f}) to achieve 100% funding."
        )
        if horizon_years <= 5:
            actions.append(
                f"Alternatively, extending the target horizon by 1–2 years will allow compounding to cover the ₹{abs(shortfall):,.2f} gap without increasing SIP."
            )
        actions.append("Preserve configured risk category: Do NOT switch to higher-risk speculative assets.")

    elif status_upper == "SIGNIFICANTLY_UNDERFUNDED":
        gap = max(Decimal("0.00"), required_sip - current_sip)
        actions.append(
            f"Significant funding gap detected (₹{abs(shortfall):,.2f}). Increase monthly SIP to ₹{required_sip:,.2f}/mo (an increase of ₹{gap:,.2f}/mo)."
        )
        actions.append(
            "Adopt an annual 10% step-up SIP strategy to align contributions with future income growth."
        )
        actions.append(
            f"Consider re-evaluating the nominal target corpus or extending the goal horizon by 3+ years."
        )
        actions.append("Strict Risk Rule: Portfolio risk must NOT be increased to chase returns.")

    elif status_upper == "NOT_FEASIBLE":
        actions.append(
            f"Goal is severely underfunded relative to the {horizon_years}-year timeframe (covers < 40% of inflation-adjusted target)."
        )
        actions.append(
            f"Bridging this gap requires ₹{required_sip:,.2f}/mo. Recommend extending the investment horizon or reducing target size."
        )
        actions.append(
            "Prioritize higher-ranking life goals (e.g. emergency fund and retirement) before committing to this discretionary goal."
        )
        actions.append("Avoid high-risk instruments or unrealistic return expectations.")

    return actions
