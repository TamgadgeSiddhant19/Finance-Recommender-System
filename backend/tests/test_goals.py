import pytest
from httpx import AsyncClient
from app.core.config import settings
from tests.conftest import make_auth_headers


@pytest.mark.asyncio
async def test_create_and_get_financial_goals(client: AsyncClient):
    """Verify creating multiple financial goals and retrieving them for an authenticated user."""
    # 1. Unauthenticated request must return 401
    unauth_res = await client.get(f"{settings.API_V1_STR}/goals/1")
    assert unauth_res.status_code == 401

    # 2. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "goals_user@example.in", "password": "password123"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]
    headers = make_auth_headers(user_id)

    # 3. Create Goal 1: House Purchase
    goal1_payload = {
        "user_id": user_id,
        "goal_type": "house",
        "target_amount": "5000000.00",
        "current_amount": "500000.00",
        "target_years": 7,
        "priority": "high",
    }
    g1_res = await client.post(f"{settings.API_V1_STR}/goals", json=goal1_payload, headers=headers)
    assert g1_res.status_code == 201
    g1_data = g1_res.json()
    assert g1_data["goal_type"] == "house"
    assert float(g1_data["target_amount"]) == 5000000.00
    assert g1_data["priority"] == "high"

    # 4. Create Goal 2: Retirement
    goal2_payload = {
        "user_id": user_id,
        "goal_type": "retirement",
        "target_amount": "20000000.00",
        "current_amount": "1000000.00",
        "target_years": 25,
        "priority": "medium",
    }
    g2_res = await client.post(f"{settings.API_V1_STR}/goals", json=goal2_payload, headers=headers)
    assert g2_res.status_code == 201

    # 5. Retrieve Goals for User
    get_res = await client.get(f"{settings.API_V1_STR}/goals/{user_id}", headers=headers)
    assert get_res.status_code == 200
    goals = get_res.json()
    assert len(goals) == 2
    types = [g["goal_type"] for g in goals]
    assert "house" in types
    assert "retirement" in types

    # 6. Retrieve via /goals/me
    me_res = await client.get(f"{settings.API_V1_STR}/goals/me", headers=headers)
    assert me_res.status_code == 200
    assert len(me_res.json()) == 2
