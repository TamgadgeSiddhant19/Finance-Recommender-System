from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.database.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.enums import RiskTolerance, InvestmentExperience
from app.schemas.financial_profile import (
    FinancialProfileBase,
    FinancialProfileCreate,
    FinancialProfileResponse,
    FinancialProfileUpdate,
)

router = APIRouter()


@router.get(
    "/profile/me",
    response_model=FinancialProfileResponse,
    summary="Get financial profile for currently authenticated user",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Retrieve stored financial profile for the authenticated user.
    """
    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found for the authenticated user. Please create one.",
        )
    return profile


@router.put(
    "/profile/me",
    response_model=FinancialProfileResponse,
    summary="Create or update financial profile for currently authenticated user",
)
@router.post(
    "/profile/me",
    response_model=FinancialProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update financial profile for currently authenticated user",
)
async def update_my_profile(
    profile_in: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Idempotently creates or updates the authenticated user's financial profile in Neon PostgreSQL.
    """
    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    existing = profile_res.scalar_one_or_none()

    update_data = {k: v for k, v in profile_in.model_dump(exclude_unset=True).items() if v is not None}

    if existing:
        for field, value in update_data.items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new profile with default baseline values for missing fields
    new_profile = FinancialProfile(
        user_id=current_user.id,
        age=update_data.get("age", 30),
        monthly_income=update_data.get("monthly_income", Decimal("100000.00")),
        monthly_expenses=update_data.get("monthly_expenses", Decimal("50000.00")),
        total_savings=update_data.get("total_savings", Decimal("300000.00")),
        monthly_investment_capacity=update_data.get("monthly_investment_capacity", Decimal("35000.00")),
        total_debt=update_data.get("total_debt", Decimal("0.00")),
        risk_tolerance=update_data.get("risk_tolerance", RiskTolerance.moderate),
        investment_experience=update_data.get("investment_experience", InvestmentExperience.intermediate),
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile


@router.post(
    "/profile",
    response_model=FinancialProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update financial profile",
)
async def create_or_update_profile(
    profile_in: FinancialProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Create or update a financial profile for a user with strict ownership verification.
    """
    if current_user.id != profile_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify another user's financial profile.",
        )

    user_res = await db.execute(select(User).where(User.id == current_user.id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {current_user.id} not found.",
        )

    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    existing_profile = profile_res.scalar_one_or_none()

    if existing_profile:
        for field, value in profile_in.model_dump().items():
            setattr(existing_profile, field, value)
        await db.commit()
        await db.refresh(existing_profile)
        return existing_profile

    db_profile = FinancialProfile(
        **profile_in.model_dump(exclude={"user_id"}),
        user_id=current_user.id,
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile


@router.put(
    "/profile/{user_id}",
    response_model=FinancialProfileResponse,
    summary="Update financial profile by user ID",
)
async def update_profile_by_user_id(
    user_id: int,
    profile_in: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Update financial profile for a specific user ID with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify another user's financial profile.",
        )

    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    existing = profile_res.scalar_one_or_none()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial profile for user {user_id} not found.",
        )

    update_data = {k: v for k, v in profile_in.model_dump(exclude_unset=True).items() if v is not None}
    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.commit()
    await db.refresh(existing)
    return existing


@router.get(
    "/profile/{user_id}",
    response_model=FinancialProfileResponse,
    summary="Get financial profile by user ID",
)
async def get_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Retrieve the financial profile for a specific user with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view another user's financial profile.",
        )

    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = profile_res.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial profile for user {user_id} not found.",
        )
    return profile
