import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Verify that GET /api/v1/health returns 200 OK with correct payload structure."""
    response = await client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project_name"] == settings.PROJECT_NAME
    assert data["environment"] == settings.ENVIRONMENT
    assert data["currency"] == "INR"
    assert data["target_market"] == "India"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_database_health_check_endpoint(client: AsyncClient):
    """Verify that GET /api/v1/health/db successfully executes a query and returns 200 OK."""
    response = await client.get(f"{settings.API_V1_STR}/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify that root endpoint GET / is responsive."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data
