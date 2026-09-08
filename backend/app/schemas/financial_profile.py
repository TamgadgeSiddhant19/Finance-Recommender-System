from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.enums import RiskTolerance, InvestmentExperience


class FinancialProfileBase(BaseModel):
    age: int = Field(..., ge=18, le=120, description="User age in years")
    monthly_income: Decimal = Field(..., ge=0, description="Monthly income in INR")
    monthly_expenses: Decimal = Field(..., ge=0, description="Monthly expenses in INR")
    total_savings: Decimal = Field(..., ge=0, description="Total current liquid savings in INR")
    monthly_investment_capacity: Decimal = Field(..., ge=0, description="Monthly capacity for investments in INR")
    total_debt: Decimal = Field(default=Decimal("0.00"), ge=0, description="Total outstanding debt in INR")
    risk_tolerance: RiskTolerance = Field(..., description="Risk tolerance tier")
    investment_experience: InvestmentExperience = Field(..., description="Investment experience level")

    @field_validator("risk_tolerance", mode="before")
    @classmethod
    def normalize_risk_tolerance(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("investment_experience", mode="before")
    @classmethod
    def normalize_investment_exp(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class FinancialProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=18, le=120, description="User age in years")
    monthly_income: Optional[Decimal] = Field(None, ge=0, description="Monthly income in INR")
    monthly_expenses: Optional[Decimal] = Field(None, ge=0, description="Monthly expenses in INR")
    total_savings: Optional[Decimal] = Field(None, ge=0, description="Total current liquid savings in INR")
    monthly_investment_capacity: Optional[Decimal] = Field(None, ge=0, description="Monthly capacity for investments in INR")
    total_debt: Optional[Decimal] = Field(None, ge=0, description="Total outstanding debt in INR")
    risk_tolerance: Optional[RiskTolerance] = Field(None, description="Risk tolerance tier")
    investment_experience: Optional[InvestmentExperience] = Field(None, description="Investment experience level")

    @field_validator("risk_tolerance", mode="before")
    @classmethod
    def normalize_risk_tolerance(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("investment_experience", mode="before")
    @classmethod
    def normalize_investment_exp(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class FinancialProfileCreate(FinancialProfileBase):
    user_id: int = Field(..., description="ID of the user this profile belongs to")


class FinancialProfileResponse(FinancialProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
