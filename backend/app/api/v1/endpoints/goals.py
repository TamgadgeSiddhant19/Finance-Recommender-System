from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.database.session import get_db
from app.models.financial_goal import FinancialGoal
from app.models.user import User
from app.schemas.financial_goal import (
    FinancialGoalBase,
    FinancialGoalCreate,
    FinancialGoalResponse,
)

router = APIRouter()


@router.get(
    "/goals/me",
    response_model=List[FinancialGoalResponse],
    summary="Get financial goals for the currently authenticated user",
)
@router.get(
    "/goals",
    response_model=List[FinancialGoalResponse],
    summary="Get financial goals for the currently authenticated user",
)
async def get_my_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[FinancialGoal]:
    """
    Retrieve all financial goals owned by the currently authenticated user.
    """
    goals_res = await db.execute(
        select(FinancialGoal)
        .where(FinancialGoal.user_id == current_user.id)
        .order_by(FinancialGoal.created_at.desc())
    )
    return list(goals_res.scalars().all())


@router.post(
    "/goals",
    response_model=FinancialGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a financial goal",
)
async def create_goal(
    goal_in: FinancialGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialGoal:
    """
    Create a new financial goal associated with the authenticated user with ownership verification.
    """
    if current_user.id != goal_in.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create goals for another user.",
        )

    user_res = await db.execute(select(User).where(User.id == current_user.id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {current_user.id} not found.",
        )

    db_goal = FinancialGoal(
        **goal_in.model_dump(exclude={"user_id"}),
        user_id=current_user.id,
    )
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal


@router.put(
    "/goals/{goal_id}",
    response_model=FinancialGoalResponse,
    summary="Update an existing financial goal",
)
async def update_goal(
    goal_id: int,
    goal_in: FinancialGoalBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FinancialGoal:
    """
    Updates an existing goal owned by the authenticated user.
    """
    stmt = select(FinancialGoal).where(FinancialGoal.id == goal_id)
    res = await db.execute(stmt)
    db_goal = res.scalar_one_or_none()
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found.",
        )

    if db_goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this goal.",
        )

    for field, value in goal_in.model_dump().items():
        setattr(db_goal, field, value)

    await db.commit()
    await db.refresh(db_goal)
    return db_goal


@router.delete(
    "/goals/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a financial goal",
)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a goal owned by the authenticated user.
    """
    stmt = select(FinancialGoal).where(FinancialGoal.id == goal_id)
    res = await db.execute(stmt)
    db_goal = res.scalar_one_or_none()
    if not db_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with id {goal_id} not found.",
        )

    if db_goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this goal.",
        )

    await db.delete(db_goal)
    await db.commit()


@router.get(
    "/goals/{user_id}",
    response_model=List[FinancialGoalResponse],
    summary="Get financial goals for a user",
)
async def get_goals(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[FinancialGoal]:
    """
    Retrieve all financial goals associated with a specific user with ownership check.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view another user's financial goals.",
        )

    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    goals_res = await db.execute(
        select(FinancialGoal)
        .where(FinancialGoal.user_id == user_id)
        .order_by(FinancialGoal.created_at.desc())
    )
    return list(goals_res.scalars().all())
