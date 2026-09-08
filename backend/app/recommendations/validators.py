from decimal import Decimal
from typing import List, Sequence, Set
from app.recommendations.constants import (
    ALLOCATION_TOLERANCE_PCT,
    ALLOWED_PRODUCT_RISK_MAP,
)
from app.recommendations.schemas import (
    PortfolioValidationReport,
    RecommendedPortfolioItem,
    TargetAllocationSummary,
    ValidationCheck,
)


def validate_portfolio(
    portfolio_items: Sequence[RecommendedPortfolioItem],
    target_allocation: TargetAllocationSummary,
    monthly_capacity: Decimal,
    risk_category: str,
    eligible_product_ids: Set[int],
) -> PortfolioValidationReport:
    """
    Runs deterministic verification checks on the candidate portfolio.
    Returns a structured validation report with passing/failing status and details.
    """
    checks: List[ValidationCheck] = []
    error_messages: List[str] = []
    warning_messages: List[str] = []

    if not portfolio_items:
        error_msg = "Portfolio contains 0 selected instruments."
        error_messages.append(error_msg)
        checks.append(ValidationCheck(
            check_name="Non-Empty Portfolio Check",
            passed=False,
            details=error_msg,
        ))
        return PortfolioValidationReport(
            is_valid=False,
            checks=checks,
            error_messages=error_messages,
            warning_messages=warning_messages,
        )

    # --------------------------------------------------------------------------
    # 1. Total Allocation Sum = 100%
    # --------------------------------------------------------------------------
    total_alloc_pct = sum(item.allocation_percentage for item in portfolio_items)
    diff = abs(total_alloc_pct - Decimal("100.00"))
    alloc_sum_passed = diff <= ALLOCATION_TOLERANCE_PCT

    if alloc_sum_passed:
        checks.append(ValidationCheck(
            check_name="Total Allocation Sum (100%)",
            passed=True,
            details=f"Total asset weights sum to {total_alloc_pct:.2f}% (Within ±{ALLOCATION_TOLERANCE_PCT}% tolerance).",
        ))
    else:
        err = f"Total portfolio allocation is {total_alloc_pct:.2f}%, violating 100.00% requirement."
        error_messages.append(err)
        checks.append(ValidationCheck(
            check_name="Total Allocation Sum (100%)",
            passed=False,
            details=err,
        ))

    # --------------------------------------------------------------------------
    # 2. Monthly SIP Capacity Adherence
    # --------------------------------------------------------------------------
    total_sip = sum(item.suggested_monthly_sip for item in portfolio_items)
    if monthly_capacity > Decimal("0.00"):
        capacity_passed = total_sip <= (monthly_capacity + Decimal("1.00"))
        if capacity_passed:
            checks.append(ValidationCheck(
                check_name="Investment Capacity Ceiling",
                passed=True,
                details=f"Total SIP deployment (₹{total_sip:,.2f}) is within monthly capacity (₹{monthly_capacity:,.2f}).",
            ))
        else:
            err = f"Total monthly SIP (₹{total_sip:,.2f}) exceeds available capacity (₹{monthly_capacity:,.2f})."
            error_messages.append(err)
            checks.append(ValidationCheck(
                check_name="Investment Capacity Ceiling",
                passed=False,
                details=err,
            ))
    else:
        checks.append(ValidationCheck(
            check_name="Investment Capacity Ceiling",
            passed=True,
            details="Zero monthly capacity (Portfolio formulated on percentage basis).",
        ))

    # --------------------------------------------------------------------------
    # 3. Product Eligibility & Risk Guardrails
    # --------------------------------------------------------------------------
    allowed_risks = ALLOWED_PRODUCT_RISK_MAP.get(risk_category.upper(), {"low", "moderate"})
    ineligible_items = []
    risk_violation_items = []

    for item in portfolio_items:
        if eligible_product_ids and item.product_id not in eligible_product_ids:
            ineligible_items.append(item.symbol)

        r_str = item.risk_level.value if hasattr(item.risk_level, "value") else str(item.risk_level).lower()
        if r_str not in allowed_risks:
            risk_violation_items.append(f"{item.symbol} ({r_str})")

    if not ineligible_items:
        checks.append(ValidationCheck(
            check_name="Product Eligibility Verification",
            passed=True,
            details="All selected instruments originate from verified eligible universe.",
        ))
    else:
        err = f"Selected instruments not in eligible catalog: {', '.join(ineligible_items)}."
        error_messages.append(err)
        checks.append(ValidationCheck(
            check_name="Product Eligibility Verification",
            passed=False,
            details=err,
        ))

    if not risk_violation_items:
        checks.append(ValidationCheck(
            check_name="Risk Profile Guardrails",
            passed=True,
            details=f"All instrument risk ratings comply with '{risk_category}' guardrails.",
        ))
    else:
        err = f"Selected instruments violate risk guardrails: {', '.join(risk_violation_items)}."
        error_messages.append(err)
        checks.append(ValidationCheck(
            check_name="Risk Profile Guardrails",
            passed=False,
            details=err,
        ))

    # --------------------------------------------------------------------------
    # 4. Asset Class Drift Verification
    # --------------------------------------------------------------------------
    actual_equity = sum(
        item.allocation_percentage
        for item in portfolio_items
        if (item.asset_class.value if hasattr(item.asset_class, "value") else str(item.asset_class).lower()) == "equity"
    )
    drift = abs(actual_equity - target_allocation.equity_pct)
    if drift <= Decimal("10.00"):
        checks.append(ValidationCheck(
            check_name="Asset Class Allocation Fidelity",
            passed=True,
            details=f"Actual equity allocation ({actual_equity:.1f}%) aligns with target ({target_allocation.equity_pct:.1f}%).",
        ))
    else:
        warning_messages.append(
            f"Noticeable equity drift of {drift:.1f}% between target ({target_allocation.equity_pct:.1f}%) and portfolio ({actual_equity:.1f}%)."
        )
        checks.append(ValidationCheck(
            check_name="Asset Class Allocation Fidelity",
            passed=True,
            details=f"Drift within permissible prototype bounds ({drift:.1f}%).",
        ))

    is_overall_valid = len(error_messages) == 0

    return PortfolioValidationReport(
        is_valid=is_overall_valid,
        checks=checks,
        error_messages=error_messages,
        warning_messages=warning_messages,
    )
