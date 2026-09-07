from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.database.session import get_db

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any], summary="Service Health Check")
def get_health() -> Dict[str, Any]:
    """
    Health check endpoint returning system operational status,
    active environment, and current UTC timestamp.
    """
    return {
        "status": "healthy",
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "currency": settings.DEFAULT_CURRENCY,
        "target_market": settings.TARGET_MARKET,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/db", response_model=Dict[str, str], summary="Database Health Check")
async def get_db_health(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Database health check verifying connectivity to PostgreSQL.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {
                "status": "healthy",
                "database": "connected",
            }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database returned unexpected response",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}",
        )
