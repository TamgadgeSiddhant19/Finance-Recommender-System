"""
Domain Exceptions for Financial Goals Feasibility & Projection Engine.
"""


class GoalError(Exception):
    """Base exception for all goal-related operations."""

    def __init__(self, message: str, goal_id: int | None = None):
        super().__init__(message)
        self.message = message
        self.goal_id = goal_id


class GoalNotFoundError(GoalError):
    """Raised when a goal record cannot be found by ID."""

    def __init__(self, goal_id: int):
        super().__init__(f"Financial Goal with ID {goal_id} not found.", goal_id)


class GoalAccessForbiddenError(GoalError):
    """Raised when a user attempts to access a goal belonging to another user."""

    def __init__(self, goal_id: int, user_id: int):
        super().__init__(
            f"User {user_id} does not have authorization to access goal {goal_id}.",
            goal_id,
        )
        self.user_id = user_id


class InvalidGoalParametersError(GoalError):
    """Raised when goal calculation inputs are invalid or mathematically impossible."""

    def __init__(self, reason: str, goal_id: int | None = None):
        super().__init__(f"Invalid goal calculation parameters: {reason}", goal_id)
        self.reason = reason
