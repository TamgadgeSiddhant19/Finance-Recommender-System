from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.database.session import get_db
from app.financial_data.models import FinancialProduct
from app.models.user import User
from app.recommendations.schemas import (
    RecommendationHistoryItem,
    RecommendationResponse,
    RecommendationSimulateRequest,
)
from app.recommendations.service import RecommendationService

router = APIRouter()


@router.post(
    "/recommendations/simulate",
    response_model=RecommendationResponse,
    summary="Stateless simulation of recommendation engine for calculators or wizards",
)
async def simulate_recommendation(
    req: RecommendationSimulateRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Executes real-time recommendation calculations without requiring existing user
    or persistence, allowing client calculators and onboarding wizards to preview allocations.
    """
    products = req.available_products
    if not products:
        from sqlalchemy import select
        res = await db.execute(select(FinancialProduct))
        products = list(res.scalars().all())

    return RecommendationService.generate_recommendation(
        profile=req.profile,
        goals=req.goals,
        available_products=products,
        user_id=None,
    )


@router.post(
    "/recommendations/me",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and persist portfolio recommendation for currently authenticated user",
)
async def generate_my_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Generates and saves a validated recommendation for the authenticated user.
    """
    try:
        return await RecommendationService.generate_and_save_for_user(db=db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/recommendations/me",
    response_model=List[RecommendationHistoryItem],
    summary="Retrieve recommendation history for currently authenticated user",
)
async def get_my_recommendation_history(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RecommendationHistoryItem]:
    """
    Retrieves past recommendations for the authenticated user.
    """
    return await RecommendationService.get_user_recommendation_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )


@router.get(

    "/recommendations/me/latest",
    response_model=RecommendationResponse,
    summary="Retrieve latest generated recommendation for currently authenticated user",
)
async def get_my_latest_recommendation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Retrieves the most recently generated recommendation for the authenticated user.
    """
    history = await RecommendationService.get_user_recommendation_history(
        db=db,
        user_id=current_user.id,
        limit=1,
    )
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendation has been generated yet for this account.",
        )
    rec = await RecommendationService.get_recommendation_by_id(
        db=db,
        user_id=current_user.id,
        recommendation_id=history[0].id,
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Latest recommendation details could not be loaded.",
        )
    return rec



@router.post(
    "/recommendations/{user_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and persist deterministic portfolio recommendation for a user",
)
async def generate_user_recommendation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Evaluates the user's financial profile, goals, risk assessment, and available
    financial instruments to construct a 100% deterministic, explainable, and validated
    investment portfolio recommendation, saving an audit trail in the database with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to generate recommendations for another user.",
        )

    try:
        return await RecommendationService.generate_and_save_for_user(db=db, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendation: {str(e)}",
        )


@router.get(
    "/recommendations/{user_id}",
    response_model=List[RecommendationHistoryItem],
    summary="Retrieve recommendation history for a user",
)
async def get_user_recommendations(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RecommendationHistoryItem]:
    """
    Retrieves summary records of historically generated portfolio recommendations for a user with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view another user's recommendations.",
        )

    return await RecommendationService.get_user_recommendation_history(
        db=db,
        user_id=user_id,
        limit=limit,
    )


@router.get(
    "/recommendations/{user_id}/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Retrieve a specific historical recommendation by ID",
)
async def get_recommendation_by_id(
    user_id: int,
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """
    Retrieves full details including selected instruments, weights, and selection rationales
    for a specific saved recommendation with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view another user's recommendations.",
        )

    rec = await RecommendationService.get_recommendation_by_id(
        db=db,
        user_id=user_id,
        recommendation_id=recommendation_id,
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID {recommendation_id} not found for user {user_id}.",
        )
    return rec
