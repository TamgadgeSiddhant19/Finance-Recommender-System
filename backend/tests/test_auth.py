import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Verify that a user can successfully register and receive a JWT token."""
    payload = {
        "email": "rahul.sharma@example.in",
        "password": "SecurePassword123!",
        "full_name": "Rahul Sharma",
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rahul.sharma@example.in"
    assert data["user"]["full_name"] == "Rahul Sharma"
    assert data["user"]["is_active"] is True
    assert "password" not in data["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    """Verify that registering with an existing email returns 400 Bad Request."""
    payload = {
        "email": "priya.patel@example.in",
        "password": "Password123!",
        "full_name": "Priya Patel",
    }
    res1 = await client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post(f"{settings.API_V1_STR}/auth/register", json=payload)
    assert res2.status_code == 400
    detail = res2.json()["detail"].lower()
    assert "already registered" in detail or "already exists" in detail


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Verify that a registered user can log in and receive a valid JWT token."""
    register_payload = {
        "email": "amit.kumar@example.in",
        "password": "MySecretPassword123",
        "full_name": "Amit Kumar",
    }
    await client.post(f"{settings.API_V1_STR}/auth/register", json=register_payload)

    login_payload = {
        "email": "amit.kumar@example.in",
        "password": "MySecretPassword123",
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "amit.kumar@example.in"


@pytest.mark.asyncio
async def test_login_invalid_password_fails(client: AsyncClient):
    """Verify that an invalid password returns 401 Unauthorized."""
    register_payload = {
        "email": "neha.gupta@example.in",
        "password": "CorrectPassword123",
    }
    await client.post(f"{settings.API_V1_STR}/auth/register", json=register_payload)

    login_payload = {
        "email": "neha.gupta@example.in",
        "password": "WrongPassword456",
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/login", json=login_payload)
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "incorrect" in detail or "invalid" in detail


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(client: AsyncClient):
    """Verify that logging in with an unknown email returns 401 Unauthorized."""
    login_payload = {
        "email": "unknown.user@example.in",
        "password": "SomePassword123",
    }
    response = await client.post(f"{settings.API_V1_STR}/auth/login", json=login_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_endpoint(client: AsyncClient):
    """Verify that /auth/me returns the current user profile when authenticated."""
    register_payload = {
        "email": "vikram.singh@example.in",
        "password": "Password789!",
        "full_name": "Vikram Singh",
    }
    reg_res = await client.post(f"{settings.API_V1_STR}/auth/register", json=register_payload)
    token = reg_res.json()["access_token"]

    # Request with valid token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get(f"{settings.API_V1_STR}/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "vikram.singh@example.in"
    assert me_data["full_name"] == "Vikram Singh"

    # Request without token
    unauth_res = await client.get(f"{settings.API_V1_STR}/auth/me")
    assert unauth_res.status_code == 401


@pytest.mark.asyncio
async def test_profile_me_route(client: AsyncClient):
    """Verify /profile/me creates/retrieves/updates the authenticated user's profile."""
    # Register user
    reg = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "ananya.das@example.in", "password": "Password123!"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update profile via /profile/me
    profile_data = {
        "age": 28,
        "monthly_income": 95000,
        "monthly_expenses": 40000,
        "total_savings": 350000,
        "monthly_investment_capacity": 35000,
        "total_debt": 0,
        "risk_tolerance": "MODERATE",
        "investment_experience": "INTERMEDIATE",
    }
    put_res = await client.put(f"{settings.API_V1_STR}/profile/me", json=profile_data, headers=headers)
    if put_res.status_code != 200:
        print("PUT /profile/me error detail:", put_res.json())
    assert put_res.status_code == 200
    assert float(put_res.json()["monthly_income"]) == 95000
    assert put_res.json()["age"] == 28

    # Fetch profile via /profile/me
    get_res = await client.get(f"{settings.API_V1_STR}/profile/me", headers=headers)
    assert get_res.status_code == 200
    assert float(get_res.json()["monthly_income"]) == 95000


@pytest.mark.asyncio
async def test_cross_user_isolation_profile_and_goals(client: AsyncClient):
    """Verify that User A cannot access or modify User B's profile and goals."""
    # Register User A
    user_a_res = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "user_a@example.in", "password": "PasswordA123!"},
    )
    user_a_token = user_a_res.json()["access_token"]
    user_a_id = user_a_res.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {user_a_token}"}

    # Register User B
    user_b_res = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": "user_b@example.in", "password": "PasswordB123!"},
    )
    user_b_token = user_b_res.json()["access_token"]
    user_b_id = user_b_res.json()["user"]["id"]
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # Setup User B's profile
    b_profile = {
        "user_id": user_b_id,
        "age": 35,
        "monthly_income": 150000,
        "monthly_expenses": 60000,
        "total_savings": 1000000,
        "monthly_investment_capacity": 60000,
        "total_debt": 200000,
        "risk_tolerance": "AGGRESSIVE",
        "investment_experience": "ADVANCED",
    }
    await client.post(f"{settings.API_V1_STR}/profile", json=b_profile, headers=headers_b)

    # Setup User B's goal
    b_goal = {
        "user_id": user_b_id,
        "goal_type": "RETIREMENT",
        "target_amount": 20000000,
        "current_amount": 1000000,
        "target_years": 20,
        "priority": "HIGH",
    }
    await client.post(f"{settings.API_V1_STR}/goals", json=b_goal, headers=headers_b)

    # User A tries to GET User B's profile -> 403 Forbidden
    res = await client.get(f"{settings.API_V1_STR}/profile/{user_b_id}", headers=headers_a)
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()

    # User A tries to PUT User B's profile -> 403 Forbidden
    res_put = await client.put(
        f"{settings.API_V1_STR}/profile/{user_b_id}",
        json={"age": 50},
        headers=headers_a,
    )
    assert res_put.status_code == 403

    # User A tries to GET User B's goals -> 403 Forbidden
    res_goals = await client.get(f"{settings.API_V1_STR}/goals/{user_b_id}", headers=headers_a)
    assert res_goals.status_code == 403

    # User A tries to GET User B's analysis -> 403 Forbidden
    res_analysis = await client.get(f"{settings.API_V1_STR}/analysis/{user_b_id}", headers=headers_a)
    assert res_analysis.status_code == 403

    # User A tries to GET User B's recommendations -> 403 Forbidden
    res_recs = await client.get(f"{settings.API_V1_STR}/recommendations/{user_b_id}", headers=headers_a)
    assert res_recs.status_code == 403
