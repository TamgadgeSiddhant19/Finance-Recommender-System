from decimal import Decimal
from app.schemas.enums import GoalType, InvestmentExperience, Priority, RiskTolerance
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase
from app.services.asset_allocation import calculate_asset_allocation
from app.services.financial_health import calculate_financial_health
from app.services.goal_analyzer import analyze_single_goal, calculate_goal_feasibility
from app.services.risk_scoring import calculate_risk_assessment


def test_financial_health_healthy_emergency_runway():
    profile = FinancialProfileBase(
        age=32,
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("500000.00"),
        monthly_investment_capacity=Decimal("40000.00"),
        total_debt=Decimal("300000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    health = calculate_financial_health(profile)
    assert health.monthly_surplus == Decimal("100000.00")
    assert health.emergency_fund_runway_months == Decimal("10.0")
    assert health.emergency_fund_status == "HEALTHY"
    assert health.target_emergency_fund == Decimal("300000.00")
    assert health.emergency_fund_gap == Decimal("0.00")
    assert health.debt_to_income_ratio == Decimal("0.17")
    assert health.surplus_to_income_ratio == Decimal("66.7")


def test_financial_health_deficient_emergency_fund():
    profile = FinancialProfileBase(
        age=26,
        monthly_income=Decimal("60000.00"),
        monthly_expenses=Decimal("40000.00"),
        total_savings=Decimal("40000.00"),  # Only 1 month runway
        monthly_investment_capacity=Decimal("10000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.aggressive,
        investment_experience=InvestmentExperience.beginner,
    )
    health = calculate_financial_health(profile)
    assert health.emergency_fund_runway_months == Decimal("1.0")
    assert health.emergency_fund_status == "DEFICIENT"
    assert health.target_emergency_fund == Decimal("240000.00")
    assert health.emergency_fund_gap == Decimal("200000.00")


def test_risk_scoring_moderate_profile():
    # User's exact prompt profile: Age 32, moderate tolerance, intermediate exp, 10 mos runway
    profile = FinancialProfileBase(
        age=32,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("40000.00"),
        total_savings=Decimal("400000.00"),
        monthly_investment_capacity=Decimal("20000.00"),
        total_debt=Decimal("100000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    assessment = calculate_risk_assessment(profile)
    assert 55 <= assessment.risk_score <= 68
    assert assessment.risk_category == "MODERATE"
    assert assessment.stated_tolerance == RiskTolerance.moderate


def test_risk_scoring_conservative_and_aggressive_categories():
    # Conservative profile
    cons_profile = FinancialProfileBase(
        age=62,
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("100000.00"),
        monthly_investment_capacity=Decimal("10000.00"),
        total_debt=Decimal("2000000.00"),  # Heavy debt
        risk_tolerance=RiskTolerance.conservative,
        investment_experience=InvestmentExperience.beginner,
    )
    cons_res = calculate_risk_assessment(cons_profile)
    assert cons_res.risk_score <= 35
    assert cons_res.risk_category == "CONSERVATIVE"

    # Aggressive profile
    agg_profile = FinancialProfileBase(
        age=24,
        monthly_income=Decimal("200000.00"),
        monthly_expenses=Decimal("60000.00"),
        total_savings=Decimal("800000.00"),
        monthly_investment_capacity=Decimal("80000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.aggressive,
        investment_experience=InvestmentExperience.advanced,
    )
    agg_res = calculate_risk_assessment(agg_profile)
    assert agg_res.risk_score >= 66
    assert agg_res.risk_category in ["AGGRESSIVE", "VERY_AGGRESSIVE"]


def test_asset_allocation_moderate_sip_math():
    profile = FinancialProfileBase(
        age=30,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("45000.00"),
        total_savings=Decimal("300000.00"),
        monthly_investment_capacity=Decimal("20000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    allocation = calculate_asset_allocation(profile, "MODERATE")
    assert allocation.constraints.equity_max_pct == Decimal("60.0")
    assert allocation.constraints.debt_min_pct == Decimal("30.0")
    assert allocation.total_monthly_investment == Decimal("20000.00")

    # Verify sum of SIPs matches total capacity exactly
    total_sip = sum(item.monthly_sip_amount for item in allocation.recommended_sip_breakdown)
    assert total_sip == Decimal("20000.00")

    # Check breakdown amounts for Moderate (55% Eq = 11,000, 35% Debt = 7,000, 10% Gold = 2,000)
    items = {item.asset_class: item.monthly_sip_amount for item in allocation.recommended_sip_breakdown}
    assert items["Domestic Equities"] == Decimal("11000.00")
    assert items["Debt & Fixed Income"] == Decimal("7000.00")
    assert items["Gold & Commodities"] == Decimal("2000.00")


def test_goal_analyzer_short_and_long_term_compounding():
    # 1. Short-term goal: Emergency fund / car in 2 years
    short_goal = FinancialGoalBase(
        goal_type=GoalType.emergency_fund,
        target_amount=Decimal("600000.00"),
        current_amount=Decimal("100000.00"),
        target_years=2,
        priority=Priority.high,
    )
    res_short = analyze_single_goal(short_goal)
    assert res_short.horizon_category == "Short-Term (<3 years)"
    assert res_short.expected_annual_return_pct == Decimal("6.50")
    assert res_short.required_monthly_sip > Decimal("0.00")

    # 2. Long-term goal: Retirement in 25 years
    long_goal = FinancialGoalBase(
        goal_type=GoalType.retirement,
        target_amount=Decimal("20000000.00"),  # 2 Crore INR
        current_amount=Decimal("500000.00"),
        target_years=25,
        priority=Priority.high,
    )
    res_long = analyze_single_goal(long_goal)
    assert res_long.horizon_category == "Long-Term (>7 years)"
    assert res_long.expected_annual_return_pct == Decimal("11.50")
    # Current 5 Lakh compounding at 11.5% over 25 years should yield > 70 Lakhs
    assert res_long.projected_future_value_from_current > Decimal("7000000.00")
    assert res_long.required_monthly_sip > Decimal("0.00")


def test_goal_feasibility_coverage():
    goal1 = FinancialGoalBase(
        goal_type=GoalType.house,
        target_amount=Decimal("3000000.00"),
        current_amount=Decimal("300000.00"),
        target_years=5,
        priority=Priority.high,
    )
    goal2 = FinancialGoalBase(
        goal_type=GoalType.education,
        target_amount=Decimal("1500000.00"),
        current_amount=Decimal("100000.00"),
        target_years=10,
        priority=Priority.medium,
    )

    # Test with abundant capacity
    report_funded = calculate_goal_feasibility([goal1, goal2], Decimal("100000.00"))
    assert report_funded.is_fully_funded is True
    assert report_funded.monthly_capacity_surplus_deficit > Decimal("0.00")
    assert report_funded.funding_coverage_pct >= Decimal("100.00")

    # Test with tight/deficit capacity
    report_deficit = calculate_goal_feasibility([goal1, goal2], Decimal("10000.00"))
    assert report_deficit.is_fully_funded is False
    assert report_deficit.monthly_capacity_surplus_deficit < Decimal("0.00")
    assert report_deficit.funding_coverage_pct < Decimal("100.00")
