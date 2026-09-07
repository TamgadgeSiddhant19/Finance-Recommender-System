import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_get_user_analysis_end_to_end(client: AsyncClient):
    """Verify GET /api/v1/analysis/{user_id} produces comprehensive financial analysis."""
    # 1. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "analysis_user@example.in", "password": "password123"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    # 2. Create Profile
    profile_payload = {
        "user_id": user_id,
        "age": 32,
        "monthly_income": "120000.00",
        "monthly_expenses": "50000.00",
        "total_savings": "500000.00",
        "monthly_investment_capacity": "35000.00",
        "total_debt": "100000.00",
        "risk_tolerance": "moderate",
        "investment_experience": "intermediate",
    }
    prof_res = await client.post(f"{settings.API_V1_STR}/profile", json=profile_payload)
    assert prof_res.status_code == 201

    # 3. Create Goal
    goal_payload = {
        "user_id": user_id,
        "goal_type": "house",
        "target_amount": "6000000.00",
        "current_amount": "600000.00",
        "target_years": 8,
        "priority": "high",
    }
    g_res = await client.post(f"{settings.API_V1_STR}/goals", json=goal_payload)
    assert g_res.status_code == 201

    # 4. Request Analysis
    analysis_res = await client.get(f"{settings.API_V1_STR}/analysis/{user_id}")
    assert analysis_res.status_code == 200
    data = analysis_res.json()

    assert data["user_id"] == user_id
    assert data["currency"] == "INR"

    # Verify Health
    health = data["financial_health"]
    assert float(health["monthly_surplus"]) == 70000.00
    assert float(health["emergency_fund_runway_months"]) == 10.0
    assert health["emergency_fund_status"] == "HEALTHY"

    # Verify Risk
    risk = data["risk_assessment"]
    assert risk["risk_category"] == "MODERATE"
    assert 50 <= risk["risk_score"] <= 70

    # Verify Asset Allocation
    alloc = data["asset_allocation"]
    assert float(alloc["total_monthly_investment"]) == 35000.00
    assert len(alloc["recommended_sip_breakdown"]) > 0

    # Verify Goal Analysis
    goals_data = data["goal_analysis"]
    assert len(goals_data["individual_goals"]) == 1
    assert goals_data["individual_goals"][0]["goal_type"] == "house"
    assert float(goals_data["total_required_monthly_sip"]) > 0


@pytest.mark.asyncio
async def test_get_analysis_missing_profile(client: AsyncClient):
    """Verify 404 when user has no financial profile."""
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "noprofile@example.in", "password": "password123"},
    )
    user_id = user_res.json()["id"]

    res = await client.get(f"{settings.API_V1_STR}/analysis/{user_id}")
    assert res.status_code == 404
    assert "Financial profile not found" in res.json()["detail"]


@pytest.mark.asyncio
async def test_simulate_analysis_endpoint(client: AsyncClient):
    """Verify stateless simulation via POST /api/v1/analysis/simulate."""
    sim_payload = {
        "profile": {
            "age": 29,
            "monthly_income": "90000.00",
            "monthly_expenses": "40000.00",
            "total_savings": "250000.00",
            "monthly_investment_capacity": "25000.00",
            "total_debt": "0.00",
            "risk_tolerance": "aggressive",
            "investment_experience": "intermediate",
        },
        "goals": [
            {
                "goal_type": "wealth_creation",
                "target_amount": "5000000.00",
                "current_amount": "100000.00",
                "target_years": 10,
                "priority": "medium",
            }
        ],
    }

    res = await client.post(f"{settings.API_V1_STR}/analysis/simulate", json=sim_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["financial_health"]["emergency_fund_status"] == "HEALTHY"
    assert data["risk_assessment"]["risk_category"] in ["MODERATE", "AGGRESSIVE"]
    assert len(data["goal_analysis"]["individual_goals"]) == 1
