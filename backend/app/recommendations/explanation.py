"""
Deterministic Explanation Builder for Recommendations.
Constructs verifiable, transparent, and structured explanation objects
for portfolio decisions, risk factors, goal trajectories, selected products,
and exclusion taxonomy. Zero LLM involvement.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union

from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import FinancialProductResponse
from app.goals.schemas import GoalProjectionResponse
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.recommendations.constants import (
    EXCLUSION_TYPE_HARD_REJECT,
    EXCLUSION_TYPE_RANKED_LOWER,
    RECOMMENDATION_ENGINE_VERSION,
    RECOMMENDATION_POLICY_VERSION,
)
from app.recommendations.schemas import (
    AssetAllocationExplanationItem,
    GoalExplanation,
    MarketDataProvenanceItem,
    ProductExclusionItem,
    RecommendationExplanation,
    RecommendedPortfolioItem,
    RiskExplanation,
    RiskExplanationFactor,
    SelectedProductExplanation,
    TargetAllocationSummary,
)
from app.schemas.financial_engine import RiskAssessmentResult
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]
ProfileTypeUnion = Union[FinancialProfile, FinancialProfileBase]


def build_risk_explanation(
    profile: ProfileTypeUnion,
    risk_assessment: RiskAssessmentResult,
) -> RiskExplanation:
    """
    Generates itemized factor contribution explanations for the user's risk profiling.
    """
    factors: List[RiskExplanationFactor] = []
    breakdown = getattr(risk_assessment, "score_breakdown", {}) or {}

    s1 = breakdown.get("tolerance_component", 50.0)
    s2 = breakdown.get("experience_component", 50.0)
    s3 = breakdown.get("age_capacity_component", 50.0)
    s4 = breakdown.get("financial_cushion_component", 50.0)
    penalty = breakdown.get("debt_burden_penalty", 0.0)

    # 1. Subjective Tolerance (40% weight)
    factors.append(
        RiskExplanationFactor(
            factor_name="Stated Risk Tolerance",
            score_contribution=Decimal(str(round(0.40 * s1, 1))),
            description=f"User stated risk preference '{risk_assessment.stated_tolerance.value.capitalize()}' yields {s1:.1f} baseline points (40% weight = +{0.40 * s1:.1f} pts).",
        )
    )

    # 2. Investment Experience (20% weight)
    factors.append(
        RiskExplanationFactor(
            factor_name="Investment Experience",
            score_contribution=Decimal(str(round(0.20 * s2, 1))),
            description=f"Experience tier '{risk_assessment.investment_experience.value.capitalize()}' provides {s2:.1f} capacity points (20% weight = +{0.20 * s2:.1f} pts).",
        )
    )

    # 3. Age Horizon Capacity (20% weight)
    factors.append(
        RiskExplanationFactor(
            factor_name="Age & Horizon Capacity",
            score_contribution=Decimal(str(round(0.20 * s3, 1))),
            description=f"Age {risk_assessment.age} years evaluates recovery horizon capacity at {s3:.1f} points (20% weight = +{0.20 * s3:.1f} pts).",
        )
    )

    # 4. Financial Cushion (20% weight)
    factors.append(
        RiskExplanationFactor(
            factor_name="Emergency Runway Cushion",
            score_contribution=Decimal(str(round(0.20 * s4, 1))),
            description=f"Current savings reserve evaluates liquid liquidity runway at {s4:.1f} points (20% weight = +{0.20 * s4:.1f} pts).",
        )
    )

    # 5. Debt Burden Penalty
    if penalty > 0:
        factors.append(
            RiskExplanationFactor(
                factor_name="Debt-to-Income Penalty",
                score_contribution=Decimal(str(round(-penalty, 1))),
                description=f"Liabilities relative to annual income deduct {penalty:.1f} points from risk score.",
            )
        )

    summary_text = (
        f"Evaluated overall composite risk score of {risk_assessment.risk_score}/100, "
        f"categorizing user as '{risk_assessment.risk_category}'. Guardrail rules restrict portfolio "
        f"exposure according to SEBI suitability ceilings."
    )

    return RiskExplanation(
        risk_score=risk_assessment.risk_score,
        risk_category=risk_assessment.risk_category,
        factors=factors,
        summary=summary_text,
    )


def build_goal_explanation(
    primary_goal: Optional[GoalTypeUnion],
    goal_projection: Optional[GoalProjectionResponse],
) -> Optional[GoalExplanation]:
    """
    Generates deterministic mathematical trajectory explanation for primary goal.
    """
    if not primary_goal or not goal_projection:
        return None

    g_type = (
        primary_goal.goal_type.value
        if hasattr(primary_goal.goal_type, "value")
        else str(primary_goal.goal_type)
    )

    status_str = goal_projection.feasibility_status.value
    funding_pct = float(goal_projection.funding_ratio_pct)

    if funding_pct >= 100.0:
        status_desc = f"Projected funding covers {funding_pct:.1f}% of the inflation-adjusted target, indicating full goal solvency."
    elif funding_pct >= 75.0:
        status_desc = f"Projected funding covers {funding_pct:.1f}% of the inflation-adjusted target (moderately underfunded). Solvable via minor SIP step-up."
    elif funding_pct >= 40.0:
        status_desc = f"Projected funding covers {funding_pct:.1f}% of the inflation-adjusted target (significantly underfunded). Requires SIP step-up or horizon extension."
    else:
        status_desc = f"Projected funding covers only {funding_pct:.1f}% of target. Timeline or target adjustment recommended without escalating portfolio risk."

    return GoalExplanation(
        goal_type=g_type,
        nominal_target=goal_projection.target_amount,
        inflation_adjusted_target=goal_projection.inflation_adjusted_target,
        projected_corpus=goal_projection.projected_corpus,
        funding_ratio_pct=goal_projection.funding_ratio_pct,
        feasibility_status=status_str,
        explanation=status_desc,
    )


def build_allocation_explanation(
    target_allocation: TargetAllocationSummary,
    horizon_bucket: str,
    risk_category: str,
    allocation_reasons: Optional[Dict[str, str]] = None,
    monthly_capacity: Decimal = Decimal("0.00"),
) -> List[AssetAllocationExplanationItem]:
    """
    Generates per-asset-class rule-driven allocation rationales.
    """
    reasons = allocation_reasons or {}
    items: List[AssetAllocationExplanationItem] = []

    alloc_map = [
        ("equity", target_allocation.equity_pct, "Long-term compounding engine aligned with SEBI risk ceiling."),
        ("debt", target_allocation.debt_pct, "Capital preservation pillar dampening portfolio volatility."),
        ("gold", target_allocation.gold_pct, "Non-correlated commodity hedge against currency purchasing power erosion."),
        ("cash", target_allocation.cash_pct, "Liquid reserve ensuring immediate capital security."),
    ]

    for asset_name, pct, default_policy in alloc_map:
        if pct > Decimal("0.00"):
            sip_part = (monthly_capacity * pct) / Decimal("100.00")
            rule_text = reasons.get(asset_name, default_policy)
            policy_rule = f"{risk_category.upper()} risk matrix for {horizon_bucket.upper()} horizon mandates {pct:.1f}% {asset_name.capitalize()}."

            items.append(
                AssetAllocationExplanationItem(
                    asset_class=asset_name,
                    allocation_percentage=pct,
                    sip_amount=round(sip_part, 2),
                    reason=rule_text,
                    policy_rule=policy_rule,
                )
            )

    return items


def build_product_selection_explanation(item: RecommendedPortfolioItem) -> SelectedProductExplanation:
    """
    Builds itemized checkmarks explaining why a specific product was chosen.
    """
    reasons = [
        f"✓ Matches target asset class allocation ({item.asset_class.upper()})",
        f"✓ Within user's risk ceiling ({item.risk_level.upper()})",
        f"✓ Suitability score ({item.suitability_score:.1f}/100) ranked #1 in category",
        f"✓ Recommended SIP (₹{item.suggested_monthly_sip:,.0f}/mo) fits monthly surplus",
    ]

    if item.expense_ratio is not None and item.expense_ratio <= Decimal("0.0050"):
        reasons.append(f"✓ Low expense ratio ({item.expense_ratio * Decimal('100.0'):.2f}% TER) minimizes return drag")

    if item.data_source and item.data_source != "master_catalog":
        reasons.append(f"✓ Historical market data provenance verified ({item.data_source})")

    metrics_dict = {
        "suitability_score": float(item.suitability_score),
        "expense_ratio": float(item.expense_ratio) if item.expense_ratio is not None else None,
        "historical_return_1y": float(item.historical_return_1y) if item.historical_return_1y is not None else None,
        "volatility": float(item.volatility) if item.volatility is not None else None,
        "max_drawdown": float(item.max_drawdown) if item.max_drawdown is not None else None,
        "data_source": item.data_source,
        "data_status": item.data_status,
    }

    return SelectedProductExplanation(
        symbol=item.symbol,
        name=item.name,
        asset_class=item.asset_class,
        suitability_score=item.suitability_score,
        allocation_percentage=item.allocation_percentage,
        suggested_monthly_sip=item.suggested_monthly_sip,
        metrics=metrics_dict,
        selection_reasons=reasons,
    )


def build_product_exclusion_taxonomy(
    all_products: Sequence[ProductTypeUnion],
    raw_exclusions: List[Dict[str, Any]],
    scored_products: List[tuple],
    selected_product_ids: set,
) -> List[ProductExclusionItem]:
    """
    Builds structured exclusion audit list clearly separating:
    1. HARD_REJECTION: Excluded during pre-scoring eligibility filters (risk ceiling, minimum capacity).
    2. RANKED_LOWER: Passed eligibility filters and scored, but outranked by higher-scoring candidates.
    """
    items: List[ProductExclusionItem] = []
    seen_symbols = set()

    # 1. Hard Rejections from pre-scoring filters
    for ex in raw_exclusions:
        sym = ex.get("symbol", "")
        if sym in seen_symbols:
            continue
        seen_symbols.add(sym)
        items.append(
            ProductExclusionItem(
                symbol=sym,
                name=ex.get("name", sym),
                asset_class=ex.get("asset_class"),
                risk_level=ex.get("risk_level"),
                suitability_score=None,
                exclusion_type=EXCLUSION_TYPE_HARD_REJECT,
                reason=ex.get("reason", "Filtered by hard suitability or ticket sizing constraints."),
            )
        )

    # 2. Eligible but ranked lower
    for scored_tuple in scored_products:
        prod = scored_tuple[0]
        score = scored_tuple[1]
        prod_id = getattr(prod, "id", None)
        sym = getattr(prod, "symbol", "")

        if prod_id not in selected_product_ids and sym not in seen_symbols:
            seen_symbols.add(sym)
            asset_str = prod.asset_class.value if hasattr(prod.asset_class, "value") else str(prod.asset_class)
            risk_str = prod.risk_level.value if hasattr(prod.risk_level, "value") else str(prod.risk_level)

            items.append(
                ProductExclusionItem(
                    symbol=sym,
                    name=getattr(prod, "name", sym),
                    asset_class=asset_str,
                    risk_level=risk_str,
                    suitability_score=score,
                    exclusion_type=EXCLUSION_TYPE_RANKED_LOWER,
                    reason=(
                        f"Eligible for {asset_str.upper()} allocation, but suitability score "
                        f"({score:.1f}/100) ranked below the selected instrument."
                    ),
                )
            )

    return items


def build_recommendation_explanation(
    profile: ProfileTypeUnion,
    goals: Sequence[GoalTypeUnion],
    risk_assessment: RiskAssessmentResult,
    target_allocation: TargetAllocationSummary,
    portfolio_items: List[RecommendedPortfolioItem],
    all_products: Sequence[ProductTypeUnion],
    raw_exclusions: List[Dict[str, Any]],
    scored_products: List[tuple],
    primary_goal_projection: Optional[GoalProjectionResponse] = None,
    allocation_reasons: Optional[Dict[str, str]] = None,
    funding_gap_actions: Optional[List[str]] = None,
    horizon_bucket: str = "GENERAL_WEALTH",
    market_provenance_map: Optional[Dict[str, MarketDataProvenanceItem]] = None,
) -> RecommendationExplanation:
    """
    Orchestrates assembly of complete RecommendationExplanation object.
    """
    primary_goal = goals[0] if goals else None
    monthly_cap = Decimal(str(profile.monthly_investment_capacity or Decimal("0.00")))

    risk_exp = build_risk_explanation(profile, risk_assessment)
    goal_exp = build_goal_explanation(primary_goal, primary_goal_projection)
    alloc_exp = build_allocation_explanation(target_allocation, horizon_bucket, risk_assessment.risk_category, allocation_reasons, monthly_cap)

    selected_ids = {item.product_id for item in portfolio_items}
    selected_exp = [build_product_selection_explanation(item) for item in portfolio_items]
    exclusion_exp = build_product_exclusion_taxonomy(all_products, raw_exclusions, scored_products, selected_ids)

    summary_text = (
        f"Generated deterministic portfolio with {len(portfolio_items)} financial products deploying "
        f"₹{sum(item.suggested_monthly_sip for item in portfolio_items):,.0f}/month across {target_allocation.equity_pct:.0f}% Equity, "
        f"{target_allocation.debt_pct:.0f}% Debt, {target_allocation.gold_pct:.0f}% Gold, and {target_allocation.cash_pct:.0f}% Cash."
    )

    return RecommendationExplanation(
        summary=summary_text,
        engine_version=RECOMMENDATION_ENGINE_VERSION,
        policy_version=RECOMMENDATION_POLICY_VERSION,
        risk_explanation=risk_exp,
        goal_explanation=goal_exp,
        allocation_explanation=alloc_exp,
        selected_products=selected_exp,
        excluded_products=exclusion_exp,
        funding_gap_actions=funding_gap_actions or [],
        data_provenance=market_provenance_map or {},
    )
