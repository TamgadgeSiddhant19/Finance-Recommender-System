import pytest
from httpx import AsyncClient
from app.core.config import settings
from tests.conftest import make_auth_headers


@pytest.mark.asyncio
async def test_create_and_get_financial_profile(client: AsyncClient):
    """Verify creating and retrieving a financial profile for an authenticated user."""
    # 1. Unauthenticated request must return 401
    unauth_res = await client.get(f"{settings.API_V1_STR}/profile/1")
    assert unauth_res.status_code == 401

    # 2. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "profile_user@example.in", "password": "password123"},
    )
    assert user_res.status_code == 201
    user_id = user_res.json()["id"]
    headers = make_auth_headers(user_id)

    # 3. Create Financial Profile with Auth
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
    create_res = await client.post(f"{settings.API_V1_STR}/profile", json=profile_payload, headers=headers)
    assert create_res.status_code == 201
    profile_data = create_res.json()
    assert profile_data["user_id"] == user_id
    assert float(profile_data["monthly_income"]) == 125000.00
    assert profile_data["risk_tolerance"] == "moderate"
    assert profile_data["investment_experience"] == "intermediate"

    # 4. Retrieve Financial Profile with Auth
    get_res = await client.get(f"{settings.API_V1_STR}/profile/{user_id}", headers=headers)
    assert get_res.status_code == 200
    fetched_data = get_res.json()
    assert fetched_data["id"] == profile_data["id"]
    assert fetched_data["age"] == 30
    assert float(fetched_data["monthly_expenses"]) == 55000.00

    # 5. Retrieve via /profile/me
    me_res = await client.get(f"{settings.API_V1_STR}/profile/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == profile_data["id"]


@pytest.mark.asyncio
async def test_cross_user_access_forbidden(client: AsyncClient):
    """Verify that a user cannot access another user's financial profile."""
    # User 1
    u1_res = await client.post(f"{settings.API_V1_STR}/users", json={"email": "u1@test.in", "password": "password123"})
    assert u1_res.status_code == 201
    u1_id = u1_res.json()["id"]
    h1 = make_auth_headers(u1_id)

    # User 2
    u2_res = await client.post(f"{settings.API_V1_STR}/users", json={"email": "u2@test.in", "password": "password123"})
    assert u2_res.status_code == 201
    u2_id = u2_res.json()["id"]
    h2 = make_auth_headers(u2_id)


    # User 2 tries to access User 1 profile -> 403 Forbidden
    cross_res = await client.get(f"{settings.API_V1_STR}/profile/{u1_id}", headers=h2)
    assert cross_res.status_code == 403


@pytest.mark.asyncio
async def test_update_existing_financial_profile(client: AsyncClient):
    """Verify that posting a new profile for an existing user updates it."""
    # 1. Create User
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "update_user@example.in", "password": "password123"},
    )
    user_id = user_res.json()["id"]
    headers = make_auth_headers(user_id)

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
    await client.post(f"{settings.API_V1_STR}/profile", json=initial_payload, headers=headers)

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
    update_res = await client.post(f"{settings.API_V1_STR}/profile", json=updated_payload, headers=headers)
    assert update_res.status_code == 201
    updated_data = update_res.json()
    assert updated_data["age"] == 29
    assert float(updated_data["monthly_income"]) == 110000.00
    assert updated_data["risk_tolerance"] == "aggressive"


@pytest.mark.asyncio
async def test_get_profile_not_found(client: AsyncClient):
    """Verify 404 response when profile does not exist for the authenticated user."""
    user_res = await client.post(
        f"{settings.API_V1_STR}/users",
        json={"email": "noprofile@example.in", "password": "password123"},
    )
    user_id = user_res.json()["id"]
    headers = make_auth_headers(user_id)

    response = await client.get(f"{settings.API_V1_STR}/profile/{user_id}", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
