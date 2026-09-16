from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Sequence, Tuple, Union
from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import FinancialProductResponse
from app.models.financial_goal import FinancialGoal
from app.recommendations.constants import (
    WEIGHT_ASSET_CLASS_FIT,
    WEIGHT_CAPACITY_COMPATIBILITY,
    WEIGHT_COST_EFFICIENCY,
    WEIGHT_DATA_QUALITY,
    WEIGHT_GOAL_FIT,
    WEIGHT_HORIZON_FIT,
    WEIGHT_MARKET_PERFORMANCE,
    WEIGHT_RISK_FIT,
)
from app.recommendations.product_intelligence import (
    ProductIntelligenceReport,
    build_product_intelligence,
    compute_cost_efficiency,
    compute_goal_compatibility,
    compute_horizon_compatibility,
    compute_risk_compatibility,
    compute_ticket_sizing,
)
from app.recommendations.schemas import ProductSelectionReason
from app.schemas.financial_goal import FinancialGoalBase

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def calculate_risk_fit(user_risk_cat: str, product_risk_str: str) -> Tuple[Decimal, str]:
    return compute_risk_compatibility(user_risk_cat, product_risk_str)


def calculate_horizon_fit(
    asset_class_str: str,
    product_type_str: str,
    goals: Sequence[GoalTypeUnion],
) -> Tuple[Decimal, str]:
    return compute_horizon_compatibility(asset_class_str, product_type_str, goals)


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
    product_type_str: str = "",
) -> Tuple[Decimal, str]:
    return compute_cost_efficiency(expense_ratio)


def calculate_capacity_compatibility(
    minimum_investment: Decimal,
    monthly_capacity: Decimal,
) -> Tuple[Decimal, str]:
    return compute_ticket_sizing(minimum_investment, monthly_capacity)


def calculate_market_performance_fit(
    intel: ProductIntelligenceReport,
) -> Tuple[Decimal, str]:
    """
    Evaluates risk-adjusted historical market performance without return-chasing.
    Penalizes extreme volatility and large drawdowns.
    """
    if intel.historical_return_1y is None or intel.data_quality_score <= Decimal("0.00"):
        return Decimal("50.00"), "Baseline market performance rating (Historical price history unmapped/neutral)"

    ret_1y = intel.historical_return_1y
    vol = intel.volatility or Decimal("15.00")
    max_dd = intel.max_drawdown or Decimal("0.00")

    # Base score derived from 1Y return (capped to prevent extreme return chasing)
    # 0% return -> 50 score, 15% return -> 80 score, 30% return -> 95 score
    if ret_1y >= Decimal("25.00"):
        score = Decimal("90.00")
    elif ret_1y >= Decimal("12.00"):
        score = Decimal("80.00")
    elif ret_1y >= Decimal("6.00"):
        score = Decimal("70.00")
    elif ret_1y >= Decimal("0.00"):
        score = Decimal("60.00")
    else:
        score = Decimal("40.00")

    # Volatility penalty (vol > 20% drops score)
    if vol > Decimal("25.00"):
        score -= Decimal("15.00")
    elif vol > Decimal("18.00"):
        score -= Decimal("5.00")

    # Drawdown penalty (max_dd < -25% drops score)
    if max_dd < Decimal("-25.00"):
        score -= Decimal("10.00")

    score = max(Decimal("10.00"), min(Decimal("100.00"), score))
    return quantize_dec(score, 2), (
        f"1Y Return: {ret_1y:+.1f}% | Volatility: {vol:.1f}% | Max Drawdown: {max_dd:.1f}% "
        f"({intel.data_source.upper()} verified)"
    )


def score_product(
    product: ProductTypeUnion,
    user_risk_cat: str,
    monthly_capacity: Decimal,
    target_allocation_dict: dict,
    goals: Sequence[GoalTypeUnion],
    intelligence_report: Optional[ProductIntelligenceReport] = None,
) -> Tuple[Decimal, List[ProductSelectionReason], ProductIntelligenceReport]:
    """
    Computes deterministic suitability score (0 - 100), selection rationales, and intelligence report.
    """
    intel = intelligence_report or build_product_intelligence(
        product=product,
        user_risk_cat=user_risk_cat,
        monthly_capacity=monthly_capacity,
        goals=goals,
    )

    asset_str = intel.asset_class
    ptype_str = (
        product.product_type.value
        if hasattr(product.product_type, "value")
        else str(product.product_type).lower()
    )
    min_invest = Decimal(str(product.minimum_investment))
    er = intel.expense_ratio

    # 1. Component scores
    s_risk, desc_risk = calculate_risk_fit(user_risk_cat, intel.risk_level)
    s_horizon, desc_horizon = calculate_horizon_fit(asset_str, ptype_str, goals)
    s_asset, desc_asset = calculate_asset_class_fit(asset_str, target_allocation_dict)
    s_goal, desc_goal = compute_goal_compatibility(asset_str, goals)
    s_cost, desc_cost = calculate_cost_efficiency(er)
    s_compat, desc_compat = calculate_capacity_compatibility(min_invest, monthly_capacity)
    s_market, desc_market = calculate_market_performance_fit(intel)
    s_quality = intel.data_quality_score

    # 2. Weighted Sum (Weights sum to exactly 1.00)
    total_score = (
        (s_risk * WEIGHT_RISK_FIT)
        + (s_horizon * WEIGHT_HORIZON_FIT)
        + (s_asset * WEIGHT_ASSET_CLASS_FIT)
        + (s_goal * WEIGHT_GOAL_FIT)
        + (s_cost * WEIGHT_COST_EFFICIENCY)
        + (s_compat * WEIGHT_CAPACITY_COMPATIBILITY)
        + (s_market * WEIGHT_MARKET_PERFORMANCE)
        + (s_quality * WEIGHT_DATA_QUALITY)
    )
    total_score = quantize_dec(total_score, 2)

    # 3. Transparent Reasons
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
            category="Financial Goal Fit",
            description=desc_goal,
            score_contribution=quantize_dec(s_goal * WEIGHT_GOAL_FIT, 2),
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
        ProductSelectionReason(
            category="Market Performance Fit",
            description=desc_market,
            score_contribution=quantize_dec(s_market * WEIGHT_MARKET_PERFORMANCE, 2),
        ),
        ProductSelectionReason(
            category="Data Quality",
            description=f"Data verification rating: {s_quality:.0f}/100 ({intel.data_source})",
            score_contribution=quantize_dec(s_quality * WEIGHT_DATA_QUALITY, 2),
        ),
    ]

    return total_score, reasons, intel
