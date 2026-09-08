from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.enums import GoalType, Priority


class FinancialGoalBase(BaseModel):
    goal_type: GoalType = Field(..., description="Classification of the financial goal")
    target_amount: Decimal = Field(..., gt=0, description="Target financial goal amount in INR")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Currently accumulated amount in INR")
    target_years: int = Field(..., gt=0, le=100, description="Investment horizon in years")
    priority: Priority = Field(default=Priority.medium, description="Priority rank of the goal")

    @field_validator("goal_type", mode="before")
    @classmethod
    def normalize_goal_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class FinancialGoalCreate(FinancialGoalBase):
    user_id: int = Field(..., description="ID of the user this goal belongs to")


class FinancialGoalResponse(FinancialGoalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
