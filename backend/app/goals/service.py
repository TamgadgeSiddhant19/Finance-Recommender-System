"""
Goal Projection Domain Service.
Orchestrates goal and profile retrieval, ownership enforcement, and mathematical projections.
"""

from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.goals.calculator import calculate_complete_goal_projection
from app.goals.exceptions import (
    GoalAccessForbiddenError,
    GoalNotFoundError,
    InvalidGoalParametersError,
)
from app.goals.schemas import (
    GoalProjectionRequest,
    GoalProjectionResponse,
    GoalProjectionSimulateRequest,
)
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile


class GoalProjectionService:
    """
    Business service executing authenticated goal feasibility assessments.
    """

    @classmethod
    async def get_projection_for_goal(
        cls,
        db: AsyncSession,
        goal_id: int,
        user_id: int,
        overrides: Optional[GoalProjectionRequest] = None,
    ) -> GoalProjectionResponse:
        """
        Retrieves an authenticated user's goal from the database and calculates the complete projection.
        """
        stmt = select(FinancialGoal).where(FinancialGoal.id == goal_id)
        res = await db.execute(stmt)
        goal = res.scalar_one_or_none()

        if not goal:
            raise GoalNotFoundError(goal_id=goal_id)

        if goal.user_id != user_id:
            raise GoalAccessForbiddenError(goal_id=goal_id, user_id=user_id)

        # Retrieve user profile to check capacity if available
        profile_stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()

        # Monthly contribution determination
        monthly_sip = Decimal("0.00")
        if overrides and overrides.monthly_contribution is not None:
            monthly_sip = overrides.monthly_contribution
        elif profile:
            # Default to a proportionate share or user's total investment capacity
            monthly_sip = profile.monthly_investment_capacity

        expected_return = overrides.expected_annual_return if overrides else None
        inflation_rate = (
            overrides.inflation_rate if (overrides and overrides.inflation_rate is not None) else Decimal("0.06")
        )

        return calculate_complete_goal_projection(
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            horizon_years=goal.target_years,
            monthly_contribution=monthly_sip,
            expected_annual_return=expected_return,
            inflation_rate=inflation_rate,
            goal_id=goal.id,
            goal_type=goal.goal_type,
        )

    @classmethod
    def simulate_projection(
        cls,
        req: GoalProjectionSimulateRequest,
    ) -> GoalProjectionResponse:
        """
        Stateless simulation of goal projection without requiring database access or existing user state.
        """
        if req.target_years <= 0:
            raise InvalidGoalParametersError("Target timeline must be at least 1 year.")

        return calculate_complete_goal_projection(
            target_amount=req.target_amount,
            current_amount=req.current_amount,
            horizon_years=req.target_years,
            monthly_contribution=req.monthly_contribution,
            expected_annual_return=req.expected_annual_return,
            inflation_rate=req.inflation_rate,
            goal_id=None,
            goal_type=req.goal_type,
        )
