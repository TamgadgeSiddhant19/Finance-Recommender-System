"""
Product Intelligence & Suitability Analysis Engine.
Calculates normalized product intelligence features and risk-adjusted metrics
from product master data and market data history. Zero LLM involvement.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Sequence, Tuple, Union
from pydantic import BaseModel, Field

from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import FinancialProductResponse
from app.market.intelligence.analytics import (
    calculate_drawdown,
    calculate_returns,
    calculate_volatility,
)
from app.market.schemas import HistoricalCandle
from app.models.financial_goal import FinancialGoal
from app.schemas.financial_goal import FinancialGoalBase

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Rounds a Decimal to specified decimal places using ROUND_HALF_UP."""
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


class ProductIntelligenceReport(BaseModel):
    """
    Deterministic analytical features for a financial instrument.
    Integrates product catalog attributes, market history, and goal alignment.
    """

    product_id: int
    symbol: str
    name: str
    asset_class: str
    risk_level: str

    # Compatibility Scores (0 - 100)
    risk_compatibility_score: Decimal = Field(..., ge=0, le=100)
    goal_compatibility_score: Decimal = Field(..., ge=0, le=100)
    horizon_compatibility_score: Decimal = Field(..., ge=0, le=100)
    cost_efficiency_score: Decimal = Field(..., ge=0, le=100)
    ticket_sizing_score: Decimal = Field(..., ge=0, le=100)

    # Market Historical Analytics (Optional — None if unverified/unavailable)
    historical_return_1y: Optional[Decimal] = None
    historical_return_3y: Optional[Decimal] = None
    historical_return_5y: Optional[Decimal] = None
    volatility: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    current_drawdown: Optional[Decimal] = None

    # Expense & Data Provenance
    expense_ratio: Decimal = Field(default=Decimal("0.00"))
    data_quality_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    data_source: str = Field(default="master_catalog")
    data_status: str = Field(default="unavailable")
    data_as_of: Optional[datetime] = None


def compute_risk_compatibility(user_risk_cat: str, product_risk_str: str) -> Tuple[Decimal, str]:
    """Calculates risk alignment score (0 - 100)."""
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
        return Decimal("100.00"), f"Exact risk match: {product_risk_str.upper()} aligns with {user_risk_cat.upper()} profile."
    elif diff == 1:
        return Decimal("75.00"), f"Adjacent risk rating: {product_risk_str.upper()} is compliant with {user_risk_cat.upper()} profile."
    elif diff == 2:
        return Decimal("50.00"), f"Moderate risk divergence: {product_risk_str.upper()} vs {user_risk_cat.upper()} profile."
    else:
        return Decimal("25.00"), f"High risk divergence: {product_risk_str.upper()} vs {user_risk_cat.upper()} profile."


def compute_horizon_compatibility(
    asset_class_str: str,
    product_type_str: str,
    goals: Sequence[GoalTypeUnion],
) -> Tuple[Decimal, str]:
    """Calculates time horizon compatibility score (0 - 100)."""
    if not goals:
        avg_horizon = Decimal("5.0")
    else:
        horizons = [Decimal(str(g.target_years)) for g in goals if getattr(g, "target_years", 0) and g.target_years > 0]
        avg_horizon = (sum(horizons) / Decimal(len(horizons))) if horizons else Decimal("5.0")

    asset = asset_class_str.lower()
    ptype = product_type_str.lower()

    if avg_horizon < Decimal("3.0"):
        if asset in {"debt", "cash"} or ptype in {"fixed_deposit", "government_security"}:
            return Decimal("95.00"), f"Short horizon ({avg_horizon:.1f}y): Capital preservation prioritizes liquid/debt instruments."
        elif asset == "gold":
            return Decimal("65.00"), f"Short horizon ({avg_horizon:.1f}y): Moderate liquidity for gold assets."
        elif asset == "hybrid":
            return Decimal("60.00"), f"Short horizon ({avg_horizon:.1f}y): Hybrid funds carry moderate equity volatility."
        else:
            return Decimal("40.00"), f"Short horizon ({avg_horizon:.1f}y): Pure equity instruments carry market cycle risk."

    elif avg_horizon <= Decimal("5.0"):
        if asset == "hybrid":
            return Decimal("95.00"), f"Medium horizon ({avg_horizon:.1f}y): Hybrid structures provide balanced risk-adjusted growth."
        elif asset in {"equity", "gold"}:
            return Decimal("85.00"), f"Medium horizon ({avg_horizon:.1f}y): Equity and Gold provide inflation-beating compounding."
        else:
            return Decimal("75.00"), f"Medium horizon ({avg_horizon:.1f}y): Debt provides stability and volatility dampening."

    else:
        if asset == "equity" or ptype in {"index_fund", "mutual_fund", "etf", "stock"}:
            return Decimal("95.00"), f"Long horizon ({avg_horizon:.1f}y): Maximum compounding benefits from growth equities."
        elif asset in {"hybrid", "gold"}:
            return Decimal("80.00"), f"Long horizon ({avg_horizon:.1f}y): Inflation hedge and non-correlated growth."
        else:
            return Decimal("60.00"), f"Long horizon ({avg_horizon:.1f}y): Debt provides baseline liquidity anchor."


def compute_goal_compatibility(
    asset_class_str: str,
    goals: Sequence[GoalTypeUnion],
) -> Tuple[Decimal, str]:
    """Calculates goal type alignment score (0 - 100)."""
    if not goals:
        return Decimal("80.00"), "General wealth creation alignment."

    asset = asset_class_str.lower()
    goal_types = [
        g.goal_type.value if hasattr(g.goal_type, "value") else str(g.goal_type).lower()
        for g in goals
    ]

    if "emergency_fund" in goal_types:
        if asset in {"cash", "debt"}:
            return Decimal("95.00"), "High suitability for emergency reserve capital protection."
        else:
            return Decimal("45.00"), "Equity volatility is unsuitable for immediate emergency liquidity."

    if "retirement" in goal_types or "wealth_creation" in goal_types:
        if asset == "equity":
            return Decimal("95.00"), "Core compounding asset class for long-term retirement target."
        elif asset in {"gold", "debt"}:
            return Decimal("80.00"), "Diversification support for long-term retirement corpus."

    if "house" in goal_types or "education" in goal_types:
        if asset in {"debt", "hybrid", "gold"}:
            return Decimal("90.00"), "Structured asset fit for milestone target purchase."
        else:
            return Decimal("75.00"), "Growth exposure aligned with medium-term milestone."

    return Decimal("80.00"), f"Asset class {asset.upper()} aligned with user financial objective."


def compute_cost_efficiency(expense_ratio: Optional[Decimal]) -> Tuple[Decimal, str]:
    """Calculates TER cost efficiency score (0 - 100)."""
    if expense_ratio is None or expense_ratio == Decimal("0.00"):
        return Decimal("95.00"), "Zero expense drag: No management fee or sovereign instrument."

    er = Decimal(str(expense_ratio))
    if er <= Decimal("0.0025"):
        return Decimal("90.00"), f"Ultra-low expense ratio ({er * Decimal('100.0'):.2f}% TER minimizes return drag)."
    elif er <= Decimal("0.0050"):
        return Decimal("80.00"), f"Competitive expense ratio ({er * Decimal('100.0'):.2f}% TER)."
    elif er <= Decimal("0.0080"):
        return Decimal("65.00"), f"Moderate expense ratio ({er * Decimal('100.0'):.2f}% TER)."
    else:
        return Decimal("50.00"), f"Higher expense ratio ({er * Decimal('100.0'):.2f}% TER)."


def compute_ticket_sizing(minimum_investment: Decimal, monthly_capacity: Decimal) -> Tuple[Decimal, str]:
    """Calculates minimum ticket size compatibility (0 - 100)."""
    if monthly_capacity <= Decimal("0.00"):
        return Decimal("50.00"), "Baseline sizing compatibility."

    min_inv = Decimal(str(minimum_investment))
    ratio = min_inv / monthly_capacity

    if ratio <= Decimal("0.20"):
        return Decimal("95.00"), f"Highly flexible minimum ticket size (₹{min_inv:,.0f} <= 20% of monthly capacity)."
    elif ratio <= Decimal("0.50"):
        return Decimal("80.00"), f"Accessible minimum ticket size (₹{min_inv:,.0f} <= 50% of monthly capacity)."
    elif ratio <= Decimal("1.00"):
        return Decimal("60.00"), f"Full capacity deployment ticket (₹{min_inv:,.0f})."
    else:
        return Decimal("20.00"), f"High ticket size relative to monthly surplus (₹{min_inv:,.0f})."


def compute_market_intelligence_features(
    candles: List[HistoricalCandle],
) -> Tuple[
    Optional[Decimal],
    Optional[Decimal],
    Optional[Decimal],
    Optional[Decimal],
    Optional[Decimal],
    Optional[Decimal],
    Decimal,
    str,
    str,
    Optional[datetime],
]:
    """
    Extracts deterministic historical return windows, volatility, drawdown, and data quality score.
    Returns:
    (ret_1y, ret_3y, ret_5y, volatility, max_drawdown, current_drawdown, data_quality_score, data_source, data_status, data_as_of)
    """
    if not candles or len(candles) < 5:
        return (
            None,
            None,
            None,
            None,
            None,
            None,
            Decimal("0.00"),
            "master_catalog",
            "unavailable",
            None,
        )

    # Sort ascending by timestamp
    sorted_candles = sorted(candles, key=lambda c: c.timestamp)
    prices = [c.close for c in sorted_candles]
    n_bars = len(prices)

    # 1. Historical Returns across windows (approx. 252 trading days = 1Y, 756 = 3Y, 1260 = 5Y)
    ret_1y = calculate_returns(prices[-min(n_bars, 252):]) if n_bars >= 20 else None
    ret_3y = calculate_returns(prices[-min(n_bars, 756):]) if n_bars >= 500 else None
    ret_5y = calculate_returns(prices[-min(n_bars, 1260):]) if n_bars >= 1000 else None

    # 2. Risk-adjusted metrics
    vol = calculate_volatility(prices, annualize=True, trading_days=252)
    max_dd, curr_dd = calculate_drawdown(prices)

    # 3. Data quality and provenance evaluation
    if n_bars >= 250:
        data_quality = Decimal("100.00")
    elif n_bars >= 100:
        data_quality = Decimal("75.00")
    elif n_bars >= 30:
        data_quality = Decimal("50.00")
    else:
        data_quality = Decimal("25.00")

    data_src = sorted_candles[-1].data_source or "market_data"
    data_stat = sorted_candles[-1].data_status or "historical"
    data_as_of = sorted_candles[-1].timestamp

    return (
        ret_1y,
        ret_3y,
        ret_5y,
        vol,
        max_dd,
        curr_dd,
        data_quality,
        data_src,
        data_stat,
        data_as_of,
    )


def build_product_intelligence(
    product: ProductTypeUnion,
    user_risk_cat: str,
    monthly_capacity: Decimal,
    goals: Sequence[GoalTypeUnion] = (),
    candles: Optional[List[HistoricalCandle]] = None,
) -> ProductIntelligenceReport:
    """
    Orchestrates full product intelligence analysis for a single financial product.
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
    er = Decimal(str(product.expense_ratio)) if product.expense_ratio is not None else Decimal("0.00")

    # 1. Compatibility scores
    s_risk, _ = compute_risk_compatibility(user_risk_cat, risk_str)
    s_horizon, _ = compute_horizon_compatibility(asset_str, ptype_str, goals)
    s_goal, _ = compute_goal_compatibility(asset_str, goals)
    s_cost, _ = compute_cost_efficiency(er)
    s_ticket, _ = compute_ticket_sizing(min_invest, monthly_capacity)

    # 2. Market features
    (
        ret_1y,
        ret_3y,
        ret_5y,
        vol,
        max_dd,
        curr_dd,
        data_quality,
        data_src,
        data_stat,
        data_as_of,
    ) = compute_market_intelligence_features(candles or [])

    return ProductIntelligenceReport(
        product_id=product.id,
        symbol=product.symbol,
        name=product.name,
        asset_class=asset_str,
        risk_level=risk_str,
        risk_compatibility_score=s_risk,
        goal_compatibility_score=s_goal,
        horizon_compatibility_score=s_horizon,
        cost_efficiency_score=s_cost,
        ticket_sizing_score=s_ticket,
        historical_return_1y=ret_1y,
        historical_return_3y=ret_3y,
        historical_return_5y=ret_5y,
        volatility=vol,
        max_drawdown=max_dd,
        current_drawdown=curr_dd,
        expense_ratio=er,
        data_quality_score=data_quality,
        data_source=data_src,
        data_status=data_stat,
        data_as_of=data_as_of,
    )
