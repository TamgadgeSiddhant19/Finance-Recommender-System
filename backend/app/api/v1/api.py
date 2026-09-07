from fastapi import APIRouter
from app.api.v1.endpoints import (
    analysis,
    financial_products,
    goals,
    health,
    profile,
    rag,
    users,
)

api_router = APIRouter()

# Register API v1 endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(profile.router, tags=["Financial Profiles"])
api_router.include_router(goals.router, tags=["Financial Goals"])
api_router.include_router(analysis.router, tags=["Financial Analysis Engine"])
api_router.include_router(financial_products.router, tags=["Financial Products & Market Data"])
api_router.include_router(rag.router, tags=["Financial Knowledge RAG"])
