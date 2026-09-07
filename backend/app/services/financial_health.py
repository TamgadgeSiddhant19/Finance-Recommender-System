from decimal import Decimal, ROUND_HALF_UP
from typing import Union
from app.models.financial_profile import FinancialProfile
from app.schemas.financial_engine import FinancialHealthMetrics
from app.schemas.financial_profile import FinancialProfileBase


def quantize_dec(val: Decimal, places: int = 2) -> Decimal:
    """Helper to round Decimal to specific decimal places."""
    pattern = Decimal("10") ** -places
    return val.quantize(pattern, rounding=ROUND_HALF_UP)


def calculate_financial_health(profile: Union[FinancialProfileBase, FinancialProfile]) -> FinancialHealthMetrics:
    """
    Compute deterministic financial health metrics for Indian personal finance:
    - Monthly cashflow surplus
    - Emergency fund runway in months
    - Target emergency fund (6 months benchmark)
    - Debt-to-annualized-income ratio
    - Savings & investment capacity ratios
    """
    monthly_income = profile.monthly_income
    monthly_expenses = profile.monthly_expenses
    total_savings = profile.total_savings
    monthly_investment_capacity = profile.monthly_investment_capacity
    total_debt = profile.total_debt

    # 1. Cashflow Surplus
    monthly_surplus = max(Decimal("0.00"), monthly_income - monthly_expenses)

    # 2. Emergency Fund Runway (Months of expenses)
    if monthly_expenses > Decimal("0.00"):
        emergency_fund_runway_months = quantize_dec(total_savings / monthly_expenses, 1)
    else:
        emergency_fund_runway_months = Decimal("99.9")

    # 3. Target Emergency Fund (6 months benchmark for India)
    target_emergency_fund = quantize_dec(monthly_expenses * Decimal("6.00"), 2)
    emergency_fund_gap = max(Decimal("0.00"), target_emergency_fund - total_savings)

    # 4. Emergency Status Classification
    if emergency_fund_runway_months < Decimal("3.0"):
        emergency_fund_status = "DEFICIENT"
    elif emergency_fund_runway_months < Decimal("6.0"):
        emergency_fund_status = "MODERATE"
    elif emergency_fund_runway_months <= Decimal("12.0"):
        emergency_fund_status = "HEALTHY"
    else:
        emergency_fund_status = "SURPLUS"

    # 5. Debt to Annualized Income Ratio
    annual_income = monthly_income * Decimal("12.00")
    if annual_income > Decimal("0.00"):
        dti_ratio = quantize_dec(total_debt / annual_income, 2)
    else:
        dti_ratio = Decimal("0.00")

    # 6. Surplus and Investment Capacity Ratios (% of income)
    if monthly_income > Decimal("0.00"):
        surplus_ratio = quantize_dec((monthly_surplus / monthly_income) * Decimal("100.00"), 1)
        investment_ratio = quantize_dec((monthly_investment_capacity / monthly_income) * Decimal("100.00"), 1)
    else:
        surplus_ratio = Decimal("0.0")
        investment_ratio = Decimal("0.0")

    return FinancialHealthMetrics(
        monthly_surplus=quantize_dec(monthly_surplus, 2),
        emergency_fund_runway_months=emergency_fund_runway_months,
        target_emergency_fund=target_emergency_fund,
        emergency_fund_status=emergency_fund_status,
        emergency_fund_gap=quantize_dec(emergency_fund_gap, 2),
        debt_to_income_ratio=dti_ratio,
        surplus_to_income_ratio=surplus_ratio,
        investment_capacity_ratio=investment_ratio,
    )
