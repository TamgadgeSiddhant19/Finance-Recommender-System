from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Sequence, Tuple, Union
from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import FinancialProductResponse
from app.models.financial_goal import FinancialGoal
from app.recommendations.constants import (
    WEIGHT_ASSET_CLASS_FIT,
    WEIGHT_CAPACITY_COMPATIBILITY,
    WEIGHT_COST_EFFICIENCY,
    WEIGHT_HORIZON_FIT,
    WEIGHT_RISK_FIT,
)
from app.recommendations.schemas import ProductSelectionReason
from app.schemas.financial_goal import FinancialGoalBase

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def calculate_risk_fit(user_risk_cat: str, product_risk_str: str) -> Tuple[Decimal, str]:
    """Calculates risk alignment score between 0 and 100."""
    risk_rank = {
        "conservative": 1,
        "moderate": 2,
        "aggressive": 3,
        "very_aggressive": 4,
    }
    prod_risk_rank = {
        "low": 1,
        "moderate": 2,
        "high": 3,
        "very_high": 4,
    }

    u_rank = risk_rank.get(user_risk_cat.lower(), 2)
    p_rank = prod_risk_rank.get(product_risk_str.lower(), 2)
    diff = abs(u_rank - p_rank)

    if diff == 0:
        return Decimal("100.00"), f"Exact risk match ({product_risk_str.upper()} aligns with {user_risk_cat.upper()} profile)"
    elif diff == 1:
        return Decimal("75.00"), f"Adjacent risk rating ({product_risk_str.upper()} is suitable for {user_risk_cat.upper()} profile)"
    elif diff == 2:
        return Decimal("50.00"), f"Moderate risk divergence ({product_risk_str.upper()} vs {user_risk_cat.upper()})"
    else:
        return Decimal("25.00"), f"High risk divergence ({product_risk_str.upper()} vs {user_risk_cat.upper()})"


def calculate_horizon_fit(
    asset_class_str: str,
    product_type_str: str,
    goals: Sequence[GoalTypeUnion],
) -> Tuple[Decimal, str]:
    """Calculates goal investment horizon compatibility score between 0 and 100."""
    if not goals:
        avg_horizon = Decimal("5.0")  # Default medium horizon
    else:
        horizons = [Decimal(str(g.target_years)) for g in goals if g.target_years and g.target_years > 0]
        avg_horizon = (sum(horizons) / Decimal(len(horizons))) if horizons else Decimal("5.0")

    asset = asset_class_str.lower()
    ptype = product_type_str.lower()

    if avg_horizon < Decimal("3.0"):
        # Short-term horizon: prioritize debt, cash, FDs, Gov securities
        if asset in {"debt", "cash"} or ptype in {"fixed_deposit", "government_security"}:
            return Decimal("95.00"), f"Short horizon ({avg_horizon:.1f} yrs): Capital preservation prioritizes liquid/debt instruments"
        elif asset == "gold":
            return Decimal("65.00"), f"Short horizon ({avg_horizon:.1f} yrs): Moderate liquidity for gold"
        elif asset == "hybrid":
            return Decimal("60.00"), f"Short horizon ({avg_horizon:.1f} yrs): Hybrid fund carries moderate equity volatility"
        else:
            return Decimal("40.00"), f"Short horizon ({avg_horizon:.1f} yrs): Pure equity instruments carry market cycle risk"

    elif avg_horizon <= Decimal("7.0"):
        # Medium-term horizon: balanced growth
        if asset == "hybrid":
            return Decimal("95.00"), f"Medium horizon ({avg_horizon:.1f} yrs): Hybrid structures provide balanced risk-adjusted growth"
        elif asset in {"equity", "gold"}:
            return Decimal("85.00"), f"Medium horizon ({avg_horizon:.1f} yrs): Equity/Gold provide inflation-beating compounding"
        else:
            return Decimal("75.00"), f"Medium horizon ({avg_horizon:.1f} yrs): Debt provides stability and volatility dampening"

    else:
        # Long-term horizon: prioritize compounding equity
        if asset == "equity" or ptype in {"index_fund", "mutual_fund", "etf", "stock"}:
            return Decimal("95.00"), f"Long horizon ({avg_horizon:.1f} yrs): Maximum compounding benefits from equity assets"
        elif asset in {"hybrid", "gold"}:
            return Decimal("80.00"), f"Long horizon ({avg_horizon:.1f} yrs): Solid hedge and diversified growth"
        else:
            return Decimal("60.00"), f"Long horizon ({avg_horizon:.1f} yrs): Debt provides baseline liquidity"


def calculate_asset_class_fit(
    asset_class_str: str,
    target_allocation_dict: dict,
) -> Tuple[Decimal, str]:
    """Calculates asset class distribution priority score between 0 and 100."""
    asset = asset_class_str.lower()
    target_pct = Decimal(str(target_allocation_dict.get(asset, Decimal("0.00"))))

    if target_pct >= Decimal("50.00"):
        return Decimal("100.00"), f"Core asset pillar with {target_pct:.1f}% target portfolio allocation"
    elif target_pct >= Decimal("20.00"):
        return Decimal("85.00"), f"Major asset pillar with {target_pct:.1f}% target portfolio allocation"
    elif target_pct > Decimal("0.00"):
        return Decimal("70.00"), f"Satellite stabilizer with {target_pct:.1f}% target portfolio allocation"
    else:
        return Decimal("30.00"), f"Asset class has 0% target allocation in base risk model"


def calculate_cost_efficiency(
    expense_ratio: Optional[Decimal],
    product_type_str: str,
) -> Tuple[Decimal, str]:
    """Calculates cost/expense ratio efficiency score between 0 and 100."""
    if expense_ratio is None or expense_ratio == Decimal("0.00"):
        return Decimal("95.00"), "Zero expense drag (No management fee or sovereign instrument)"

    er = Decimal(str(expense_ratio))
    if er <= Decimal("0.0025"):
        return Decimal("90.00"), f"Ultra-low expense ratio ({er * Decimal('100.0'):.2f}% TER minimizes return drag)"
    elif er <= Decimal("0.0050"):
        return Decimal("80.00"), f"Competitive expense ratio ({er * Decimal('100.0'):.2f}% TER)"
    elif er <= Decimal("0.0080"):
        return Decimal("65.00"), f"Moderate expense ratio ({er * Decimal('100.0'):.2f}% TER)"
    else:
        return Decimal("50.00"), f"Higher expense ratio ({er * Decimal('100.0'):.2f}% TER)"


def calculate_capacity_compatibility(
    minimum_investment: Decimal,
    monthly_capacity: Decimal,
) -> Tuple[Decimal, str]:
    """Calculates ticket size compatibility score between 0 and 100."""
    if monthly_capacity <= Decimal("0.00"):
        return Decimal("50.00"), "Baseline compatibility evaluation"

    min_inv = Decimal(str(minimum_investment))
    ratio = min_inv / monthly_capacity

    if ratio <= Decimal("0.20"):
        return Decimal("95.00"), f"Highly flexible ticket size (₹{min_inv:,.0f} is <= 20% of monthly capacity)"
    elif ratio <= Decimal("0.50"):
        return Decimal("80.00"), f"Accessible ticket size (₹{min_inv:,.0f} is <= 50% of monthly capacity)"
    elif ratio <= Decimal("1.00"):
        return Decimal("60.00"), f"Full capacity deployment ticket (₹{min_inv:,.0f})"
    else:
        return Decimal("20.00"), f"High ticket size relative to monthly capacity (₹{min_inv:,.0f})"


def score_product(
    product: ProductTypeUnion,
    user_risk_cat: str,
    monthly_capacity: Decimal,
    target_allocation_dict: dict,
    goals: Sequence[GoalTypeUnion],
) -> Tuple[Decimal, List[ProductSelectionReason]]:
    """
    Computes deterministic suitability score (0 - 100) and selection rationales.
    """
    risk_str = (
        product.risk_level.value
        if hasattr(product.risk_level, "value")
        else str(product.risk_level).lower()
    )
    asset_str = (
        product.asset_class.value
        if hasattr(product.asset_class, "value")
        else str(product.asset_class).lower()
    )
    ptype_str = (
        product.product_type.value
        if hasattr(product.product_type, "value")
        else str(product.product_type).lower()
    )
    min_invest = Decimal(str(product.minimum_investment))
    er = Decimal(str(product.expense_ratio)) if product.expense_ratio is not None else None

    # 1. Component scores
    s_risk, desc_risk = calculate_risk_fit(user_risk_cat, risk_str)
    s_horizon, desc_horizon = calculate_horizon_fit(asset_str, ptype_str, goals)
    s_asset, desc_asset = calculate_asset_class_fit(asset_str, target_allocation_dict)
    s_cost, desc_cost = calculate_cost_efficiency(er, ptype_str)
    s_compat, desc_compat = calculate_capacity_compatibility(min_invest, monthly_capacity)

    # 2. Weighted Sum
    total_score = (
        (s_risk * WEIGHT_RISK_FIT)
        + (s_horizon * WEIGHT_HORIZON_FIT)
        + (s_asset * WEIGHT_ASSET_CLASS_FIT)
        + (s_cost * WEIGHT_COST_EFFICIENCY)
        + (s_compat * WEIGHT_CAPACITY_COMPATIBILITY)
    )
    total_score = quantize_dec(total_score, 2)

    # 3. Reasons
    reasons = [
        ProductSelectionReason(
            category="Risk Suitability",
            description=desc_risk,
            score_contribution=quantize_dec(s_risk * WEIGHT_RISK_FIT, 2),
        ),
        ProductSelectionReason(
            category="Goal Horizon Fit",
            description=desc_horizon,
            score_contribution=quantize_dec(s_horizon * WEIGHT_HORIZON_FIT, 2),
        ),
        ProductSelectionReason(
            category="Asset Class Alignment",
            description=desc_asset,
            score_contribution=quantize_dec(s_asset * WEIGHT_ASSET_CLASS_FIT, 2),
        ),
        ProductSelectionReason(
            category="Cost Efficiency",
            description=desc_cost,
            score_contribution=quantize_dec(s_cost * WEIGHT_COST_EFFICIENCY, 2),
        ),
        ProductSelectionReason(
            category="Ticket Sizing Compatibility",
            description=desc_compat,
            score_contribution=quantize_dec(s_compat * WEIGHT_CAPACITY_COMPATIBILITY, 2),
        ),
    ]

    return total_score, reasons
