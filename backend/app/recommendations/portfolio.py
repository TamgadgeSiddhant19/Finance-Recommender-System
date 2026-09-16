from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Sequence, Tuple, Union
from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductResponse,
    ProductRiskLevel,
    ProductType,
)
from app.recommendations.product_intelligence import ProductIntelligenceReport
from app.recommendations.schemas import (
    ProductSelectionReason,
    RecommendedPortfolioItem,
    TargetAllocationSummary,
)

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
ScoredProductTuple = Union[
    Tuple[ProductTypeUnion, Decimal, List[ProductSelectionReason]],
    Tuple[ProductTypeUnion, Decimal, List[ProductSelectionReason], Optional[ProductIntelligenceReport]],
]


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def construct_portfolio(
    scored_products: Sequence[ScoredProductTuple],
    target_allocation: TargetAllocationSummary,
    monthly_capacity: Decimal,
    lump_sum_capacity: Decimal = Decimal("0.00"),
) -> List[RecommendedPortfolioItem]:
    """
    Constructs an optimal candidate portfolio matching the target asset allocation.
    Ranks products within each asset bucket by suitability score and calculates exact INR amounts.
    Integrates product intelligence features into RecommendedPortfolioItem output.
    """
    if not scored_products:
        return []

    # 1. Group products by asset class
    buckets: Dict[str, List[Tuple[ProductTypeUnion, Decimal, List[ProductSelectionReason], Optional[ProductIntelligenceReport]]]] = {
        "equity": [],
        "debt": [],
        "gold": [],
        "cash": [],
    }

    for item in scored_products:
        prod = item[0]
        score = item[1]
        reasons = item[2]
        intel = item[3] if len(item) > 3 else None

        asset_str = (
            prod.asset_class.value
            if hasattr(prod.asset_class, "value")
            else str(prod.asset_class).lower()
        )
        entry = (prod, score, reasons, intel)

        if asset_str in buckets:
            buckets[asset_str].append(entry)
        elif asset_str == "hybrid":
            # Hybrid can serve equity or debt buckets if needed
            buckets["equity"].append(entry)
            buckets["debt"].append(entry)
        else:
            buckets["debt"].append(entry)

    # Sort each bucket descending by score
    for k in buckets:
        buckets[k].sort(key=lambda x: x[1], reverse=True)

    target_map = {
        "equity": target_allocation.equity_pct,
        "debt": target_allocation.debt_pct,
        "gold": target_allocation.gold_pct,
        "cash": target_allocation.cash_pct,
    }

    selected_allocations: List[dict] = []

    # 2. Allocate instruments per asset class target
    for asset_class, target_pct in target_map.items():
        if target_pct <= Decimal("0.00"):
            continue

        available = buckets.get(asset_class, [])

        # Fallback if primary bucket is empty
        if not available:
            if asset_class == "cash" and buckets["debt"]:
                available = buckets["debt"]
            elif asset_class == "gold" and buckets["debt"]:
                available = buckets["debt"]
            elif buckets["equity"]:
                available = buckets["equity"]
            elif buckets["debt"]:
                available = buckets["debt"]

        if not available:
            continue

        # Decide instrument count based on allocation weight
        if target_pct >= Decimal("50.00") and len(available) >= 2:
            # Pick top 2 instruments for diversification
            p1, score1, reasons1, intel1 = available[0]
            p2, score2, reasons2, intel2 = available[1]
            pct1 = quantize_dec(target_pct * Decimal("0.55"), 2)
            pct2 = target_pct - pct1

            selected_allocations.append({
                "product": p1,
                "score": score1,
                "reasons": reasons1,
                "intel": intel1,
                "pct": pct1,
            })
            selected_allocations.append({
                "product": p2,
                "score": score2,
                "reasons": reasons2,
                "intel": intel2,
                "pct": pct2,
            })
        else:
            # Pick top 1 instrument
            p, score, reasons, intel = available[0]
            selected_allocations.append({
                "product": p,
                "score": score,
                "reasons": reasons,
                "intel": intel,
                "pct": target_pct,
            })

    if not selected_allocations:
        return []

    # 3. Ensure total percentage sums exactly to 100.00%
    total_pct = sum(item["pct"] for item in selected_allocations)
    if total_pct != Decimal("100.00") and total_pct > Decimal("0.00"):
        diff = Decimal("100.00") - total_pct
        # Adjust largest allocation
        selected_allocations.sort(key=lambda x: x["pct"], reverse=True)
        selected_allocations[0]["pct"] += diff

    # 4. Build RecommendedPortfolioItem instances
    portfolio_items: List[RecommendedPortfolioItem] = []
    for item in selected_allocations:
        prod = item["product"]
        pct = item["pct"]
        score = item["score"]
        reasons = item["reasons"]
        intel: Optional[ProductIntelligenceReport] = item.get("intel")

        monthly_sip = quantize_dec((monthly_capacity * pct) / Decimal("100.00"), 2)
        lump_sum = quantize_dec((lump_sum_capacity * pct) / Decimal("100.00"), 2)

        # Convert enums safely
        p_type = (
            prod.product_type
            if isinstance(prod.product_type, ProductType)
            else ProductType(str(prod.product_type).lower())
        )
        a_class = (
            prod.asset_class
            if isinstance(prod.asset_class, AssetClass)
            else AssetClass(str(prod.asset_class).lower())
        )
        r_level = (
            prod.risk_level
            if isinstance(prod.risk_level, ProductRiskLevel)
            else ProductRiskLevel(str(prod.risk_level).lower())
        )

        portfolio_items.append(
            RecommendedPortfolioItem(
                product_id=prod.id,
                symbol=prod.symbol,
                name=prod.name,
                product_type=p_type,
                asset_class=a_class,
                risk_level=r_level,
                suitability_score=score,
                allocation_percentage=pct,
                suggested_monthly_sip=monthly_sip,
                suggested_lump_sum=lump_sum,
                selection_reasons=reasons,
                risk_compatibility_score=intel.risk_compatibility_score if intel else None,
                goal_compatibility_score=intel.goal_compatibility_score if intel else None,
                horizon_compatibility_score=intel.horizon_compatibility_score if intel else None,
                historical_return_1y=intel.historical_return_1y if intel else None,
                historical_return_3y=intel.historical_return_3y if intel else None,
                historical_return_5y=intel.historical_return_5y if intel else None,
                volatility=intel.volatility if intel else None,
                max_drawdown=intel.max_drawdown if intel else None,
                current_drawdown=intel.current_drawdown if intel else None,
                expense_ratio=intel.expense_ratio if intel else (prod.expense_ratio if getattr(prod, "expense_ratio", None) is not None else Decimal("0.00")),
                data_quality_score=intel.data_quality_score if intel else Decimal("0.00"),
                data_source=intel.data_source if intel else "master_catalog",
                data_status=intel.data_status if intel else "unavailable",
                data_as_of=intel.data_as_of if intel else None,
            )
        )

    # Sort final items by allocation percentage descending
    portfolio_items.sort(key=lambda x: x.allocation_percentage, reverse=True)
    return portfolio_items
