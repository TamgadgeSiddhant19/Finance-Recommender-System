"""
Comprehensive Unit and Integration Tests for Phase 7.1 Goal Feasibility & Projection Engine.
"""

from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_auth_headers
from app.goals.calculator import (
    calculate_complete_goal_projection,
    calculate_future_value_lump_sum,
    calculate_future_value_sip,
    calculate_inflation_adjusted_target,
    calculate_required_annual_return,
    calculate_required_sip,
    classify_goal_feasibility,
    get_default_expected_return,
)
from app.goals.schemas import GoalFeasibilityStatus
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.enums import (
    GoalType,
    InvestmentExperience,
    Priority,
    RiskTolerance,
)


# ---------------------------------------------------------------------------
# 1. Pure Mathematical Formulas & Edge Cases
# ---------------------------------------------------------------------------

def test_future_value_lump_sum():
    """Verify lump sum monthly compounding."""
    pv = Decimal("100000.00")
    rate = Decimal("0.10")  # 10% p.a.
    years = 5

    # FV = 100000 * (1 + 0.10/12)^60 = ~164,530.89
    fv = calculate_future_value_lump_sum(pv, rate, years)
    assert fv > Decimal("164000.00")
    assert fv < Decimal("165000.00")

    # Edge cases
    assert calculate_future_value_lump_sum(Decimal("0.00"), rate, years) == Decimal("0.00")
    assert calculate_future_value_lump_sum(pv, Decimal("0.00"), years) == pv
    assert calculate_future_value_lump_sum(pv, rate, 0) == pv


def test_future_value_sip_annuity_due():
    """Verify monthly SIP compounding using Annuity Due (beginning of period)."""
    pmt = Decimal("10000.00")
    rate = Decimal("0.12")  # 12% p.a. (1% per month)
    years = 10  # 120 months

    # FV_annuity_due = 10000 * ((1.01^120 - 1)/0.01) * 1.01 = ~2,323,390.83
    fv = calculate_future_value_sip(pmt, rate, years)
    assert fv > Decimal("2300000.00")
    assert fv < Decimal("2350000.00")

    # Zero rate edge case: PMT * months = 10000 * 120 = 1,200,000.00
    assert calculate_future_value_sip(pmt, Decimal("0.00"), years) == Decimal("1200000.00")
    assert calculate_future_value_sip(Decimal("0.00"), rate, years) == Decimal("0.00")


def test_inflation_adjusted_target():
    """Verify target corpus inflation compounding."""
    nominal = Decimal("5000000.00")
    inflation = Decimal("0.06")  # 6% p.a.
    years = 10

    # 5,000,000 * (1.06)^10 = ~8,954,238.48
    adjusted = calculate_inflation_adjusted_target(nominal, inflation, years)
    assert adjusted > Decimal("8900000.00")
    assert adjusted < Decimal("9000000.00")

    # Zero inflation
    assert calculate_inflation_adjusted_target(nominal, Decimal("0.00"), years) == nominal


def test_required_sip_calculation():
    """Verify required monthly SIP calculation to reach target."""
    target = Decimal("1000000.00")
    current = Decimal("100000.00")
    rate = Decimal("0.10")
    years = 5

    req_sip = calculate_required_sip(
        target_amount=target,
        current_amount=current,
        annual_rate=rate,
        years=years,
        inflation_rate=Decimal("0.00"),
    )
    assert req_sip > Decimal("0.00")
    assert req_sip < Decimal("15000.00")

    # When current investment already exceeds target
    achieved_sip = calculate_required_sip(
        target_amount=Decimal("100000.00"),
        current_amount=Decimal("200000.00"),
        annual_rate=rate,
        years=years,
    )
    assert achieved_sip == Decimal("0.00")


def test_required_annual_return_bisection():
    """Verify required annual return root-finding."""
    target = Decimal("1000000.00")
    current = Decimal("200000.00")
    monthly = Decimal("5000.00")
    years = 5

    req_return = calculate_required_annual_return(
        target_amount=target,
        current_amount=current,
        monthly_amount=monthly,
        years=years,
        inflation_rate=Decimal("0.00"),
    )
    assert req_return is not None
    assert req_return > Decimal("0.00")
    assert req_return < Decimal("50.00")

    # Impossible case: requires > 100% return
    impossible_return = calculate_required_annual_return(
        target_amount=Decimal("100000000.00"),
        current_amount=Decimal("1000.00"),
        monthly_amount=Decimal("100.00"),
        years=1,
    )
    assert impossible_return is None


def test_feasibility_classification_thresholds():
    """Verify feasibility status classification against exact thresholds."""
    # 1. On Track (>= 100%)
    status_on_track, ratio_on_track = classify_goal_feasibility(
        projected_corpus=Decimal("1050000.00"),
        inflation_adjusted_target=Decimal("1000000.00"),
    )
    assert status_on_track == GoalFeasibilityStatus.ON_TRACK
    assert ratio_on_track == Decimal("105.00")

    # 2. Moderately Underfunded (75% to 99.9%)
    status_mod, ratio_mod = classify_goal_feasibility(
        projected_corpus=Decimal("850000.00"),
        inflation_adjusted_target=Decimal("1000000.00"),
    )
    assert status_mod == GoalFeasibilityStatus.MODERATELY_UNDERFUNDED
    assert ratio_mod == Decimal("85.00")

    # 3. Significantly Underfunded (40% to 74.9%)
    status_sig, ratio_sig = classify_goal_feasibility(
        projected_corpus=Decimal("500000.00"),
        inflation_adjusted_target=Decimal("1000000.00"),
    )
    assert status_sig == GoalFeasibilityStatus.SIGNIFICANTLY_UNDERFUNDED
    assert ratio_sig == Decimal("50.00")

    # 4. Not Feasible (< 40%)
    status_not_f, ratio_not_f = classify_goal_feasibility(
        projected_corpus=Decimal("300000.00"),
        inflation_adjusted_target=Decimal("1000000.00"),
    )
    assert status_not_f == GoalFeasibilityStatus.NOT_FEASIBLE
    assert ratio_not_f == Decimal("30.00")


# ---------------------------------------------------------------------------
# 2. REST API Integration & Ownership Verification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_goal_projection_authenticated_flow(
    client: AsyncClient, db_session: AsyncSession
):
    # 1. Seed User
    user = User(email="projection_user@example.com", password_hash="dummy_hash")
    db_session.add(user)
    await db_session.flush()

    # 2. Seed Profile
    profile = FinancialProfile(
        user_id=user.id,
        age=30,
        monthly_income=Decimal("120000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("400000.00"),
        monthly_investment_capacity=Decimal("30000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    db_session.add(profile)

    # 3. Seed Goal
    goal = FinancialGoal(
        user_id=user.id,
        goal_type=GoalType.retirement,
        target_amount=Decimal("10000000.00"),
        current_amount=Decimal("500000.00"),
        target_years=15,
        priority=Priority.high,
    )
    db_session.add(goal)
    await db_session.commit()

    headers = make_auth_headers(user.id)

    # 4. Unauthenticated call must fail with 401
    unauth_res = await client.post(f"/api/v1/goals/{goal.id}/projection")
    assert unauth_res.status_code == 401

    # 5. Authenticated call to calculate projection
    res = await client.post(f"/api/v1/goals/{goal.id}/projection", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["goal_id"] == goal.id
    assert float(data["target_amount"]) == 10000000.00
    assert float(data["current_amount"]) == 500000.00
    assert data["horizon_years"] == 15
    assert float(data["inflation_adjusted_target"]) > 10000000.00
    assert float(data["projected_corpus"]) > 0
    assert "funding_ratio_pct" in data
    assert "feasibility_status" in data
    assert data["feasibility_status"] in [
        "ON_TRACK",
        "MODERATELY_UNDERFUNDED",
        "SIGNIFICANTLY_UNDERFUNDED",
        "NOT_FEASIBLE",
    ]
    assert len(data["recommendations"]) > 0
    assert "assumptions" in data


@pytest.mark.asyncio
async def test_api_goal_projection_cross_user_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    # 1. Create User A and Goal A
    user_a = User(email="user_a_proj@example.com", password_hash="hash_a")
    db_session.add(user_a)
    await db_session.flush()

    goal_a = FinancialGoal(
        user_id=user_a.id,
        goal_type=GoalType.house,
        target_amount=Decimal("5000000.00"),
        current_amount=Decimal("200000.00"),
        target_years=5,
        priority=Priority.high,
    )
    db_session.add(goal_a)

    # 2. Create User B
    user_b = User(email="user_b_proj@example.com", password_hash="hash_b")
    db_session.add(user_b)
    await db_session.commit()

    headers_b = make_auth_headers(user_b.id)

    # 3. User B attempting to view User A's goal projection must be forbidden (403)
    res = await client.post(f"/api/v1/goals/{goal_a.id}/projection", headers=headers_b)
    assert res.status_code == 403

    # 4. Non-existent goal ID must return 404
    res_404 = await client.post("/api/v1/goals/999999/projection", headers=headers_b)
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_api_goal_projection_stateless_simulation(client: AsyncClient):
    """Verify stateless simulation without database requirements."""
    payload = {
        "goal_type": "retirement",
        "target_amount": "5000000.00",
        "current_amount": "200000.00",
        "target_years": 10,
        "monthly_contribution": "15000.00",
        "expected_annual_return": "0.115",
        "inflation_rate": "0.06",
        "priority": "high",
    }
    res = await client.post("/api/v1/goals/projection/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["goal_id"] is None
    assert float(data["target_amount"]) == 5000000.00
    assert float(data["current_amount"]) == 200000.00
    assert float(data["monthly_contribution"]) == 15000.00
    assert data["horizon_years"] == 10
    assert float(data["expected_annual_return_pct"]) == 11.50
    assert float(data["inflation_rate_pct"]) == 6.00
    assert float(data["projected_corpus"]) > 0
    assert data["feasibility_status"] is not None
