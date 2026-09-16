"""
Comprehensive unit and integration test suite for Phase 7.2 Goal-Aware Asset Allocation Engine.
Verifies deterministic mathematical policies, horizon buckets, risk guardrails, funding gap guidance,
multi-goal prioritization, and API endpoints.
"""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import make_auth_headers

from app.financial_data.models import FinancialProduct
from app.financial_data.schemas import (
    AssetClass,
    FinancialProductResponse,
    ProductRiskLevel,
    ProductType,
)
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.recommendations.allocation import (
    determine_primary_horizon,
    generate_goal_aware_allocation_with_reasons,
    generate_target_allocation,
)
from app.recommendations.policy import (
    GoalHorizonBucket,
    GOAL_AWARE_ALLOCATION_MATRIX,
    RISK_GUARDRAILS,
    classify_horizon_bucket,
    generate_funding_gap_actions,
)
from app.recommendations.service import RecommendationService
from app.schemas.enums import (
    GoalType,
    InvestmentExperience,
    Priority,
    RiskTolerance,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase


def get_mock_products():
    return [
        FinancialProduct(
            id=1,
            symbol="NIFTY50-INDX",
            name="Nifty 50 Index Fund",
            product_type=ProductType.index_fund,
            asset_class=AssetClass.equity,
            issuer="UTI Mutual Fund",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.high,
            expense_ratio=Decimal("0.0020"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=2,
            symbol="FLEXICAP-EQ",
            name="Parag Parikh Flexi Cap Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="PPFAS Mutual Fund",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.high,
            expense_ratio=Decimal("0.0065"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=3,
            symbol="CORPBOND-DBT",
            name="ICICI Prudential Corporate Bond Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.debt,
            issuer="ICICI Prudential AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.moderate,
            expense_ratio=Decimal("0.0035"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=4,
            symbol="PPF-GOV",
            name="Public Provident Fund Scheme",
            product_type=ProductType.government_security,
            asset_class=AssetClass.debt,
            issuer="Government of India",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.low,
            expense_ratio=Decimal("0.0000"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=5,
            symbol="GOLDetf-COMM",
            name="Nippon India ETF Gold BeES",
            product_type=ProductType.etf,
            asset_class=AssetClass.gold,
            issuer="Nippon Life India AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.moderate,
            expense_ratio=Decimal("0.0050"),
            minimum_investment=Decimal("100.00"),
        ),
        FinancialProduct(
            id=6,
            symbol="LIQUID-CSH",
            name="Mirae Asset Cash Management Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.cash,
            issuer="Mirae Asset AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.low,
            expense_ratio=Decimal("0.0015"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=7,
            symbol="MIDCAP-EQ",
            name="HDFC Mid-Cap Opportunities Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="HDFC AMC",
            currency="INR",
            country="India",
            risk_level=ProductRiskLevel.very_high,
            expense_ratio=Decimal("0.0075"),
            minimum_investment=Decimal("500.00"),
        ),
    ]


# ------------------------------------------------------------------------------
# 1. Horizon Bucket & Policy Classification Tests
# ------------------------------------------------------------------------------

def test_horizon_bucket_classification():
    assert classify_horizon_bucket(1) == GoalHorizonBucket.SHORT_TERM
    assert classify_horizon_bucket(2.5) == GoalHorizonBucket.SHORT_TERM
    assert classify_horizon_bucket(3) == GoalHorizonBucket.MEDIUM_TERM
    assert classify_horizon_bucket(4.5) == GoalHorizonBucket.MEDIUM_TERM
    assert classify_horizon_bucket(5) == GoalHorizonBucket.MEDIUM_TERM
    assert classify_horizon_bucket(5.1) == GoalHorizonBucket.LONG_TERM
    assert classify_horizon_bucket(10) == GoalHorizonBucket.LONG_TERM
    assert classify_horizon_bucket(None) == GoalHorizonBucket.GENERAL_WEALTH


def test_primary_horizon_selection_priority_order():
    g_low = FinancialGoalBase(
        goal_type=GoalType.other,
        target_amount=Decimal("100000.00"),
        target_years=1,
        priority=Priority.low,
    )
    g_high = FinancialGoalBase(
        goal_type=GoalType.retirement,
        target_amount=Decimal("10000000.00"),
        target_years=15,
        priority=Priority.high,
    )
    g_med = FinancialGoalBase(
        goal_type=GoalType.house,
        target_amount=Decimal("2500000.00"),
        target_years=4,
        priority=Priority.medium,
    )

    # High priority goal must dominate horizon determination
    horizon_val, bucket = determine_primary_horizon([g_low, g_high, g_med])
    assert horizon_val == Decimal("15")
    assert bucket == GoalHorizonBucket.LONG_TERM

    # If tied priority, nearest horizon wins to safeguard sequence of returns
    g_high_near = FinancialGoalBase(
        goal_type=GoalType.emergency_fund,
        target_amount=Decimal("300000.00"),
        target_years=2,
        priority=Priority.high,
    )
    horizon_val2, bucket2 = determine_primary_horizon([g_high, g_high_near])
    assert horizon_val2 == Decimal("2")
    assert bucket2 == GoalHorizonBucket.SHORT_TERM


# ------------------------------------------------------------------------------
# 2. Goal-Aware Allocation & Exact 100% Sum Tests
# ------------------------------------------------------------------------------

@pytest.mark.parametrize("risk_cat", ["CONSERVATIVE", "MODERATE", "AGGRESSIVE", "VERY_AGGRESSIVE"])
@pytest.mark.parametrize("years", [1, 2, 3, 4, 5, 7, 12, None])
def test_all_permutations_sum_exactly_to_100(risk_cat, years):
    goals = [FinancialGoalBase(goal_type=GoalType.wealth_creation, target_amount=Decimal("1000000"), target_years=years, priority=Priority.medium)] if years else []
    alloc, reasons, bucket = generate_goal_aware_allocation_with_reasons(
        risk_category=risk_cat,
        goals=goals,
    )
    total = alloc.equity_pct + alloc.debt_pct + alloc.gold_pct + alloc.cash_pct
    assert total == Decimal("100.00"), f"Failed for {risk_cat}, years={years}: total={total}"
    assert "equity" in reasons
    assert "debt" in reasons
    assert "gold" in reasons
    assert "cash" in reasons


def test_short_term_horizon_capital_preservation():
    # Short-term horizon (<3 yrs) must curtail equity and elevate debt & cash
    short_goal = FinancialGoalBase(
        goal_type=GoalType.emergency_fund,
        target_amount=Decimal("200000.00"),
        target_years=1,
        priority=Priority.high,
    )

    # For Moderate Profile:
    alloc_mod, reasons_mod, bucket = generate_goal_aware_allocation_with_reasons(
        risk_category="MODERATE",
        goals=[short_goal],
    )
    assert bucket == GoalHorizonBucket.SHORT_TERM
    assert alloc_mod.equity_pct == Decimal("15.00")
    assert alloc_mod.debt_pct == Decimal("65.00")
    assert alloc_mod.cash_pct == Decimal("15.00")
    assert "sequence-of-returns volatility" in reasons_mod["equity"]

    # For Aggressive Profile:
    alloc_agg, _, _ = generate_goal_aware_allocation_with_reasons(
        risk_category="AGGRESSIVE",
        goals=[short_goal],
    )
    assert alloc_agg.equity_pct <= Decimal("20.00")
    assert alloc_agg.debt_pct >= Decimal("60.00")


def test_medium_term_horizon_balanced_growth():
    med_goal = FinancialGoalBase(
        goal_type=GoalType.house,
        target_amount=Decimal("2000000.00"),
        target_years=4,
        priority=Priority.high,
    )
    alloc, reasons, bucket = generate_goal_aware_allocation_with_reasons(
        risk_category="MODERATE",
        goals=[med_goal],
    )
    assert bucket == GoalHorizonBucket.MEDIUM_TERM
    assert alloc.equity_pct == Decimal("45.00")
    assert alloc.debt_pct == Decimal("45.00")
    assert alloc.gold_pct == Decimal("10.00")


def test_long_term_horizon_growth_and_guardrails():
    long_goal = FinancialGoalBase(
        goal_type=GoalType.retirement,
        target_amount=Decimal("15000000.00"),
        target_years=15,
        priority=Priority.high,
    )
    # 1. Aggressive long-term allows high equity
    alloc_agg, reasons_agg, bucket = generate_goal_aware_allocation_with_reasons(
        risk_category="AGGRESSIVE",
        goals=[long_goal],
    )
    assert bucket == GoalHorizonBucket.LONG_TERM
    assert alloc_agg.equity_pct == Decimal("75.00")
    assert alloc_agg.debt_pct == Decimal("15.00")

    # 2. Risk Guardrail: Conservative profile with 15-year goal CANNOT exceed 30% equity
    alloc_cons, reasons_cons, _ = generate_goal_aware_allocation_with_reasons(
        risk_category="CONSERVATIVE",
        goals=[long_goal],
    )
    assert alloc_cons.equity_pct <= Decimal("30.00")
    assert alloc_cons.debt_pct >= Decimal("60.00")


# ------------------------------------------------------------------------------
# 3. Feasibility & Funding-Gap Safety Tests
# ------------------------------------------------------------------------------

def test_funding_gap_actions_never_recommends_higher_risk():
    # 1. Moderately underfunded
    actions_mod = generate_funding_gap_actions(
        feasibility_status="MODERATELY_UNDERFUNDED",
        required_sip=Decimal("15000.00"),
        current_sip=Decimal("10000.00"),
        shortfall=Decimal("-300000.00"),
        horizon_years=3,
    )
    assert any("Increase monthly SIP" in a for a in actions_mod)
    assert any("Do NOT switch to higher-risk" in a for a in actions_mod)

    # 2. Significantly underfunded
    actions_sig = generate_funding_gap_actions(
        feasibility_status="SIGNIFICANTLY_UNDERFUNDED",
        required_sip=Decimal("35000.00"),
        current_sip=Decimal("10000.00"),
        shortfall=Decimal("-2500000.00"),
        horizon_years=5,
    )
    assert any("step-up SIP" in a for a in actions_sig)
    assert any("must NOT be increased to chase returns" in a for a in actions_sig)

    # 3. Not feasible
    actions_nf = generate_funding_gap_actions(
        feasibility_status="NOT_FEASIBLE",
        required_sip=Decimal("80000.00"),
        current_sip=Decimal("5000.00"),
        shortfall=Decimal("-8000000.00"),
        horizon_years=3,
    )
    assert any("extending the investment horizon" in a for a in actions_nf)
    assert any("Avoid high-risk instruments" in a for a in actions_nf)


# ------------------------------------------------------------------------------
# 4. Recommendation Orchestrator & Multi-Goal Integration Tests
# ------------------------------------------------------------------------------

def test_generate_recommendation_with_goal_awareness():
    products = get_mock_products()
    profile = FinancialProfileBase(
        age=30,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("300000.00"),
        monthly_investment_capacity=Decimal("25000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    goal = FinancialGoalBase(
        goal_type=GoalType.retirement,
        target_amount=Decimal("10000000.00"),
        current_amount=Decimal("200000.00"),
        target_years=10,
        priority=Priority.high,
    )

    rec = RecommendationService.generate_recommendation(
        profile=profile,
        goals=[goal],
        available_products=products,
    )

    assert rec.risk_category == "MODERATE"
    assert rec.goal_horizon_bucket == "LONG_TERM"
    assert rec.goal_feasibility_status in ["ON_TRACK", "MODERATELY_UNDERFUNDED", "SIGNIFICANTLY_UNDERFUNDED", "NOT_FEASIBLE"]
    assert rec.nominal_target == Decimal("10000000.00")
    assert rec.inflation_adjusted_target > Decimal("10000000.00")
    assert rec.projected_corpus is not None
    assert rec.funding_ratio is not None
    assert rec.allocation_reasons is not None
    assert len(rec.allocation_reasons) == 4
    assert len(rec.goals_breakdown) == 1
    assert rec.validation_report.is_valid is True


def test_multi_goal_priority_allocation():
    products = get_mock_products()
    profile = FinancialProfileBase(
        age=32,
        monthly_income=Decimal("120000.00"),
        monthly_expenses=Decimal("60000.00"),
        total_savings=Decimal("400000.00"),
        monthly_investment_capacity=Decimal("30000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    # High priority emergency fund (2 years) + Low priority education (1 year)
    goal_emergency = FinancialGoalBase(
        goal_type=GoalType.emergency_fund,
        target_amount=Decimal("300000.00"),
        current_amount=Decimal("100000.00"),
        target_years=2,
        priority=Priority.high,
    )
    goal_education = FinancialGoalBase(
        goal_type=GoalType.education,
        target_amount=Decimal("150000.00"),
        current_amount=Decimal("0.00"),
        target_years=1,
        priority=Priority.low,
    )

    rec = RecommendationService.generate_recommendation(
        profile=profile,
        goals=[goal_emergency, goal_education],
        available_products=products,
    )

    assert len(rec.goals_breakdown) == 2
    # High priority goal gets allocated first
    assert rec.goals_breakdown[0].goal_type == "emergency_fund"
    assert rec.goals_breakdown[0].priority == "high"
    assert rec.goals_breakdown[0].allocated_monthly_sip > Decimal("0.00")


# ------------------------------------------------------------------------------
# 5. Full API Workflow & Persistence Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recommendation_api_goal_aware_workflow(client: AsyncClient, db_session: AsyncSession):
    # 1. Seed products
    for p in get_mock_products():
        db_session.add(p)

    # 2. Seed User
    user = User(email="goal_rec_test@example.com", password_hash="dummy_hash")
    db_session.add(user)
    await db_session.flush()

    # 3. Seed Profile
    profile = FinancialProfile(
        user_id=user.id,
        age=29,
        monthly_income=Decimal("140000.00"),
        monthly_expenses=Decimal("60000.00"),
        total_savings=Decimal("400000.00"),
        monthly_investment_capacity=Decimal("35000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    db_session.add(profile)

    # 4. Seed Goal (Medium term: 4 years house)
    goal = FinancialGoal(
        user_id=user.id,
        goal_type=GoalType.house,
        target_amount=Decimal("3000000.00"),
        target_years=4,
        priority=Priority.high,
    )
    db_session.add(goal)
    await db_session.commit()

    headers = make_auth_headers(user.id)

    # 5. POST /recommendations/{user_id}
    res = await client.post(f"/api/v1/recommendations/{user.id}", headers=headers)
    assert res.status_code == 201, f"Error: {res.text}"
    data = res.json()

    assert data["goal_horizon_bucket"] == "MEDIUM_TERM"
    assert data["goal_feasibility_status"] is not None
    assert float(data["nominal_target"]) == 3000000.0
    assert data["inflation_adjusted_target"] is not None
    assert data["projected_corpus"] is not None
    assert data["funding_ratio"] is not None
    assert data["allocation_reasons"]["equity"] is not None
    assert len(data["portfolio_items"]) > 0
    assert data["validation_report"]["is_valid"] is True
    rec_id = data["recommendation_id"]

    # 6. GET /recommendations/{user_id}/{rec_id}
    get_res = await client.get(f"/api/v1/recommendations/{user.id}/{rec_id}", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["recommendation_id"] == rec_id
    assert get_data["goal_horizon_bucket"] == "MEDIUM_TERM"
    assert float(get_data["nominal_target"]) == 3000000.0
    assert len(get_data["goals_breakdown"]) >= 1
