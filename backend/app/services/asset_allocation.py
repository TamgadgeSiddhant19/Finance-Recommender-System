from decimal import Decimal, ROUND_HALF_UP
from typing import List, Union
from app.models.financial_profile import FinancialProfile
from app.schemas.financial_engine import (
    AssetAllocationBreakdown,
    AssetAllocationConstraint,
    SIPAssetAllocation,
)
from app.schemas.financial_profile import FinancialProfileBase


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def calculate_asset_allocation(
    profile: Union[FinancialProfileBase, FinancialProfile],
    risk_category: str,
) -> AssetAllocationBreakdown:
    """
    Deterministic asset allocation matrix tailored for the Indian financial ecosystem:
    - Sets strict exposure bounds for Equities, Debt, Gold, and Liquid Reserves.
    - Generates rupee-denominated monthly SIP breakdown for the user's investment capacity.
    """
    monthly_capacity = profile.monthly_investment_capacity
    monthly_expenses = profile.monthly_expenses
    recommended_emergency_buffer = quantize_dec(monthly_expenses * Decimal("6.00"), 2)

    # Matrix Definition based on Risk Category
    if risk_category == "CONSERVATIVE":
        constraints = AssetAllocationConstraint(
            equity_min_pct=Decimal("20.0"),
            equity_max_pct=Decimal("30.0"),
            debt_min_pct=Decimal("60.0"),
            debt_max_pct=Decimal("70.0"),
            gold_pct=Decimal("5.0"),
            liquid_reserve_pct=Decimal("5.0"),
        )
        base_allocations = [
            ("Domestic Equities", Decimal("25.0"), [
                "Nifty 50 Index Fund",
                "Large Cap Mutual Fund",
            ]),
            ("Debt & Fixed Income", Decimal("65.0"), [
                "Public Provident Fund (PPF)",
                "Target Maturity Debt Index Funds",
                "High-Quality Corporate Bond Funds",
                "Bank Fixed Deposits",
            ]),
            ("Gold & Commodities", Decimal("5.0"), [
                "Sovereign Gold Bonds (SGB)",
                "Gold ETFs",
            ]),
            ("Liquid / Cash Buffer", Decimal("5.0"), [
                "Liquid Mutual Funds",
                "High-Yield Savings / Sweep-in FDs",
            ]),
        ]

    elif risk_category == "MODERATE":
        constraints = AssetAllocationConstraint(
            equity_min_pct=Decimal("50.0"),
            equity_max_pct=Decimal("60.0"),
            debt_min_pct=Decimal("30.0"),
            debt_max_pct=Decimal("40.0"),
            gold_pct=Decimal("10.0"),
            liquid_reserve_pct=Decimal("0.0"),
        )
        base_allocations = [
            ("Domestic Equities", Decimal("55.0"), [
                "Nifty 50 Index Fund",
                "Flexi-Cap Mutual Fund",
                "Large & Mid-Cap Mutual Fund",
            ]),
            ("Debt & Fixed Income", Decimal("35.0"), [
                "Corporate Bond Fund",
                "Short Duration Debt Fund",
                "Public Provident Fund (PPF)",
            ]),
            ("Gold & Commodities", Decimal("10.0"), [
                "Sovereign Gold Bonds (SGB)",
                "Gold ETFs",
            ]),
        ]

    elif risk_category == "AGGRESSIVE":
        constraints = AssetAllocationConstraint(
            equity_min_pct=Decimal("70.0"),
            equity_max_pct=Decimal("80.0"),
            debt_min_pct=Decimal("10.0"),
            debt_max_pct=Decimal("20.0"),
            gold_pct=Decimal("10.0"),
            liquid_reserve_pct=Decimal("0.0"),
        )
        base_allocations = [
            ("Domestic Equities", Decimal("75.0"), [
                "Nifty 50 / Sensex Index Fund",
                "Flexi-Cap Mutual Fund",
                "Mid-Cap Fund",
                "Direct Indian Equities",
            ]),
            ("Debt & Fixed Income", Decimal("15.0"), [
                "Short Duration Debt Fund",
                "Corporate Bond Fund",
            ]),
            ("Gold & Commodities", Decimal("10.0"), [
                "Gold ETFs",
                "Sovereign Gold Bonds (SGB)",
            ]),
        ]

    else:  # VERY_AGGRESSIVE
        constraints = AssetAllocationConstraint(
            equity_min_pct=Decimal("80.0"),
            equity_max_pct=Decimal("90.0"),
            debt_min_pct=Decimal("5.0"),
            debt_max_pct=Decimal("15.0"),
            gold_pct=Decimal("5.0"),
            liquid_reserve_pct=Decimal("0.0"),
        )
        base_allocations = [
            ("Domestic Equities", Decimal("85.0"), [
                "Flexi-Cap Fund",
                "Mid-Cap Fund",
                "Small-Cap Fund",
                "Nifty 50 Index Fund",
            ]),
            ("Debt & Fixed Income", Decimal("10.0"), [
                "Dynamic Bond / Ultra Short Term Debt",
            ]),
            ("Gold & Commodities", Decimal("5.0"), [
                "Gold ETFs",
            ]),
        ]

    # Calculate Rupee amounts for monthly SIP
    sip_items: List[SIPAssetAllocation] = []
    for asset_name, pct, instruments in base_allocations:
        sip_amount = quantize_dec((monthly_capacity * pct) / Decimal("100.00"), 2)
        sip_items.append(
            SIPAssetAllocation(
                asset_class=asset_name,
                allocation_pct=pct,
                monthly_sip_amount=sip_amount,
                instrument_types=instruments,
            )
        )

    return AssetAllocationBreakdown(
        constraints=constraints,
        recommended_sip_breakdown=sip_items,
        total_monthly_investment=quantize_dec(monthly_capacity, 2),
        recommended_emergency_buffer=recommended_emergency_buffer,
    )
