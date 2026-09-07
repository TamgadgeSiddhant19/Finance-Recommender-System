from enum import Enum


class RiskTolerance(str, Enum):
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"
    very_aggressive = "very_aggressive"


class InvestmentExperience(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class GoalType(str, Enum):
    retirement = "retirement"
    house = "house"
    education = "education"
    emergency_fund = "emergency_fund"
    wealth_creation = "wealth_creation"
    other = "other"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
