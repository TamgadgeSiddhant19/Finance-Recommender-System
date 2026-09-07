from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.financial_profile import FinancialProfileCreate, FinancialProfileResponse

router = APIRouter()


@router.post("/profile", response_model=FinancialProfileResponse, status_code=status.HTTP_201_CREATED, summary="Create or update financial profile")
async def create_or_update_profile(
    profile_in: FinancialProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Create or update a financial profile for an existing user.
    """
    # Verify user exists
    user_res = await db.execute(select(User).where(User.id == profile_in.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {profile_in.user_id} not found.",
        )

    # Check if profile already exists for this user
    profile_res = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == profile_in.user_id)
    )
    existing_profile = profile_res.scalar_one_or_none()

    if existing_profile:
        # Update existing profile
        for field, value in profile_in.model_dump().items():
            setattr(existing_profile, field, value)
        await db.commit()
        await db.refresh(existing_profile)
        return existing_profile

    # Create new profile
    db_profile = FinancialProfile(**profile_in.model_dump())
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile


@router.get("/profile/{user_id}", response_model=FinancialProfileResponse, summary="Get financial profile by user ID")
async def get_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> FinancialProfile:
    """
    Retrieve the financial profile for a specific user.
    """
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
