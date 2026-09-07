import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_create_and_get_financial_profile(client: AsyncClient):
    """Verify creating and retrieving a financial profile for a user."""
    # 1. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "profile_user@example.in", "password": "password123"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]

    # 2. Create Financial Profile
    profile_payload = {
        "user_id": user_id,
        "age": 30,
        "monthly_income": "125000.00",
        "monthly_expenses": "55000.00",
        "total_savings": "500000.00",
        "monthly_investment_capacity": "45000.00",
        "total_debt": "0.00",
        "risk_tolerance": "moderate",
        "investment_experience": "intermediate",
    }
    create_res = await client.post(f"{settings.API_V1_STR}/profile", json=profile_payload)
    assert create_res.status_code == 201
    profile_data = create_res.json()
    assert profile_data["user_id"] == user_id
    assert float(profile_data["monthly_income"]) == 125000.00
    assert profile_data["risk_tolerance"] == "moderate"
    assert profile_data["investment_experience"] == "intermediate"

    # 3. Retrieve Financial Profile
    get_res = await client.get(f"{settings.API_V1_STR}/profile/{user_id}")
    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["id"] == profile_data["id"]
    assert fetched_data["age"] == 30
    assert float(fetched_data["monthly_expenses"]) == 55000.00


@pytest.mark.asyncio
async def test_update_existing_financial_profile(client: AsyncClient):
    """Verify that posting a new profile for an existing user updates it (1-to-1)."""
    # 1. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "update_user@example.in", "password": "password123"},
    )
    user_id = user_res.json()["id"]

    # 2. Create Initial Profile
    initial_payload = {
        "user_id": user_id,
        "age": 28,
        "monthly_income": "80000.00",
        "monthly_expenses": "40000.00",
        "total_savings": "200000.00",
        "monthly_investment_capacity": "25000.00",
        "total_debt": "100000.00",
        "risk_tolerance": "conservative",
        "investment_experience": "beginner",
    }
    await client.post(f"{settings.API_V1_STR}/profile", json=initial_payload)

    # 3. Post Updated Profile
    updated_payload = {
        "user_id": user_id,
        "age": 29,
        "monthly_income": "110000.00",
        "monthly_expenses": "45000.00",
        "total_savings": "400000.00",
        "monthly_investment_capacity": "40000.00",
        "total_debt": "0.00",
        "risk_tolerance": "aggressive",
        "investment_experience": "intermediate",
    }
    update_res = await client.post(f"{settings.API_V1_STR}/profile", json=updated_payload)
    assert update_res.status_code == 201
    updated_data = update_res.json()
    assert updated_data["age"] == 29
    assert float(updated_data["monthly_income"]) == 110000.00
    assert updated_data["risk_tolerance"] == "aggressive"


@pytest.mark.asyncio
async def test_get_profile_not_found(client: AsyncClient):
    """Verify 404 response when profile does not exist."""
    response = await client.get(f"{settings.API_V1_STR}/profile/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_profile_nonexistent_user(client: AsyncClient):
    """Verify 404 response when creating profile for nonexistent user."""
    payload = {
        "user_id": 99999,
        "age": 25,
        "monthly_income": "50000.00",
        "monthly_expenses": "25000.00",
        "total_savings": "100000.00",
        "monthly_investment_capacity": "15000.00",
        "total_debt": "0.00",
        "risk_tolerance": "moderate",
        "investment_experience": "beginner",
    }
    response = await client.post(f"{settings.API_V1_STR}/profile", json=payload)
    assert response.status_code == 404
