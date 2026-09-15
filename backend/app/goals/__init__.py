"""
Financial Goals Feasibility & Projection Engine Module.
"""

from app.goals.calculator import (
    calculate_complete_goal_projection,
    calculate_future_value_lump_sum,
    calculate_future_value_sip,
    calculate_inflation_adjusted_target,
    calculate_required_annual_return,
    calculate_required_sip,
    classify_goal_feasibility,
    get_default_expected_return,
)
from app.goals.exceptions import (
    GoalAccessForbiddenError,
    GoalError,
    GoalNotFoundError,
    InvalidGoalParametersError,
)
from app.goals.schemas import (
    CalculationAssumptions,
    GoalFeasibilityStatus,
    GoalProjectionRequest,
    GoalProjectionResponse,
    GoalProjectionSimulateRequest,
)
from app.goals.service import GoalProjectionService

__all__ = [
    "calculate_complete_goal_projection",
    "calculate_future_value_lump_sum",
    "calculate_future_value_sip",
    "calculate_inflation_adjusted_target",
    "calculate_required_annual_return",
    "calculate_required_sip",
    "classify_goal_feasibility",
    "get_default_expected_return",
    "GoalError",
    "GoalNotFoundError",
    "GoalAccessForbiddenError",
    "InvalidGoalParametersError",
    "GoalFeasibilityStatus",
    "CalculationAssumptions",
    "GoalProjectionRequest",
    "GoalProjectionResponse",
    "GoalProjectionSimulateRequest",
    "GoalProjectionService",
]
