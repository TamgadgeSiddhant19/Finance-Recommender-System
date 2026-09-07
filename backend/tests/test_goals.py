import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_create_and_get_financial_goals(client: AsyncClient):
    """Verify creating multiple financial goals and retrieving them for a user."""
    # 1. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "goals_user@example.in", "password": "password123"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    # 2. Create Goal 1: House Purchase
    goal1_payload = {
        "user_id": user_id,
        "goal_type": "house",
        "target_amount": "5000000.00",
        "current_amount": "500000.00",
        "target_years": 7,
        "priority": "high",
    }
    g1_res = await client.post(f"{settings.API_V1_STR}/goals", json=goal1_payload)
    assert g1_res.status_code == 201
    g1_data = g1_res.json()
    assert g1_data["goal_type"] == "house"
    assert float(g1_data["target_amount"]) == 5000000.00
    assert g1_data["priority"] == "high"

    # 3. Create Goal 2: Retirement
    goal2_payload = {
        "user_id": user_id,
        "goal_type": "retirement",
        "target_amount": "20000000.00",
        "current_amount": "1000000.00",
        "target_years": 25,
        "priority": "medium",
    }
    g2_res = await client.post(f"{settings.API_V1_STR}/goals", json=goal2_payload)
    assert g2_res.status_code == 201

    # 4. Retrieve Goals for User
    get_res = await client.get(f"{settings.API_V1_STR}/goals/{user_id}")
    assert get_res.status_code == 200
    goals = get_res.json()
    assert len(goals) == 2
    types = [g["goal_type"] for g in goals]
    assert "house" in types
    assert "retirement" in types


@pytest.mark.asyncio
async def test_get_goals_for_nonexistent_user(client: AsyncClient):
    """Verify 404 response when querying goals for a non-existent user."""
    response = await client.get(f"{settings.API_V1_STR}/goals/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_goal_for_nonexistent_user(client: AsyncClient):
    """Verify 404 response when creating a goal for a non-existent user."""
    payload = {
        "user_id": 99999,
        "goal_type": "emergency_fund",
        "target_amount": "300000.00",
        "current_amount": "50000.00",
        "target_years": 1,
        "priority": "high",
    }
    response = await client.post(f"{settings.API_V1_STR}/goals", json=payload)
    assert response.status_code == 404
