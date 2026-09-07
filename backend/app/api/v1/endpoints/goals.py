from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.financial_goal import FinancialGoal
from app.models.user import User
from app.schemas.financial_goal import FinancialGoalCreate, FinancialGoalResponse

router = APIRouter()


@router.post("/goals", response_model=FinancialGoalResponse, status_code=status.HTTP_201_CREATED, summary="Create a financial goal")
async def create_goal(
    goal_in: FinancialGoalCreate,
    db: AsyncSession = Depends(get_db),
) -> FinancialGoal:
    """
    Create a new financial goal associated with an existing user.
    """
    # Verify user exists
    user_res = await db.execute(select(User).where(User.id == goal_in.user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {goal_in.user_id} not found.",
        )

    db_goal = FinancialGoal(**goal_in.model_dump())
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal


@router.get("/goals/{user_id}", response_model=List[FinancialGoalResponse], summary="Get financial goals for a user")
async def get_goals(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[FinancialGoal]:
    """
    Retrieve all financial goals associated with a specific user.
    """
    # Verify user exists
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    goals_res = await db.execute(
        select(FinancialGoal).where(FinancialGoal.user_id == user_id).order_by(FinancialGoal.created_at.desc())
    )
    return list(goals_res.scalars().all())
