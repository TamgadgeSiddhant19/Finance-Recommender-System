from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.database.session import get_db
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.financial_engine import (
    ComprehensiveFinancialAnalysisResponse,
    SimulationRequest,
)
from app.services.engine import FinancialEngineService

router = APIRouter()


@router.get(
    "/analysis/me",
    response_model=ComprehensiveFinancialAnalysisResponse,
    summary="Generate comprehensive financial analysis for currently authenticated user",
)
async def get_my_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComprehensiveFinancialAnalysisResponse:
    """
    Retrieve stored financial profile and goals for the authenticated user,
    and execute the pure deterministic financial engine.
    """
    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found for authenticated user. Please create a profile first.",
        )

    goals_res = await db.execute(
        select(FinancialGoal).where(FinancialGoal.user_id == current_user.id).order_by(FinancialGoal.created_at.desc())
    )
    goals = list(goals_res.scalars().all())

    return FinancialEngineService.analyze_profile_and_goals(
        profile=profile,
        goals=goals,
        user_id=current_user.id,
    )


@router.get(
    "/analysis/{user_id}",
    response_model=ComprehensiveFinancialAnalysisResponse,
    summary="Generate comprehensive deterministic financial analysis for a user",
)
async def get_user_analysis(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComprehensiveFinancialAnalysisResponse:
    """
    Retrieve stored financial profile and goals for an existing user,
    and execute the pure deterministic financial engine (with ownership enforcement).
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view another user's financial analysis.",
        )

    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial profile not found for user {user_id}. Please create a profile first.",
        )

    goals_res = await db.execute(
        select(FinancialGoal).where(FinancialGoal.user_id == user_id).order_by(FinancialGoal.created_at.desc())
    )
    goals = list(goals_res.scalars().all())

    return FinancialEngineService.analyze_profile_and_goals(
        profile=profile,
        goals=goals,
        user_id=user_id,
    )


@router.post(
    "/analysis/simulate",
    response_model=ComprehensiveFinancialAnalysisResponse,
    summary="Stateless simulation of financial health, risk scoring, asset allocation and goals",
)
def simulate_analysis(
    req: SimulationRequest,
) -> ComprehensiveFinancialAnalysisResponse:
    """
    Execute real-time deterministic financial calculations without requiring
    prior database storage (ideal for calculators, simulators, and onboarding wizards).
    """
    return FinancialEngineService.analyze_profile_and_goals(
        profile=req.profile,
        goals=req.goals,
        user_id=None,
    )
