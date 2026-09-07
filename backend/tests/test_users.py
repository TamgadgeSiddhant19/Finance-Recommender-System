import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    """Verify that a user can be successfully registered."""
    payload = {
        "email": "investor@example.in",
        "password": "secure_password_123",
    }
    response = await client.post(f"{settings.API_V1_STR}/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "investor@example.in"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_create_duplicate_user_fails(client: AsyncClient):
    """Verify that duplicate user registration returns 400 Bad Request."""
    payload = {
        "email": "duplicate@example.in",
        "password": "secure_password_123",
    }
    # First creation
    res1 = await client.post(f"{settings.API_V1_STR}/users", json=payload)
    assert res1.status_code == 201

    # Second creation with same email
    res2 = await client.post(f"{settings.API_V1_STR}/users", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: AsyncClient):
    """Verify that invalid email format is rejected by Pydantic validation."""
    payload = {
        "email": "not-an-email",
        "password": "secure_password_123",
    }
    response = await client.post(f"{settings.API_V1_STR}/users", json=payload)
    assert response.status_code == 422
