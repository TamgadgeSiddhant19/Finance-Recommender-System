from typing import Optional, Sequence, Union
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.schemas.financial_engine import (
    ComprehensiveFinancialAnalysisResponse,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase
from app.services.asset_allocation import calculate_asset_allocation
from app.services.financial_health import calculate_financial_health
from app.services.goal_analyzer import calculate_goal_feasibility
from app.services.risk_scoring import calculate_risk_assessment


class FinancialEngineService:
    """
    Orchestration service for the deterministic financial engine:
    Evaluates health, computes multi-factor risk score, generates asset allocation matrix,
    and runs goal feasibility analysis.
    """

    @staticmethod
    def analyze_profile_and_goals(
        profile: Union[FinancialProfileBase, FinancialProfile],
        goals: Sequence[Union[FinancialGoalBase, FinancialGoal]],
        user_id: Optional[int] = None,
    ) -> ComprehensiveFinancialAnalysisResponse:
        # 1. Financial Health Subsystem
        health_metrics = calculate_financial_health(profile)

        # 2. Risk Scoring Subsystem
        risk_result = calculate_risk_assessment(profile)

        # 3. Asset Allocation Matrix Subsystem
        allocation_breakdown = calculate_asset_allocation(
            profile=profile,
            risk_category=risk_result.risk_category,
        )

        # 4. Goal Feasibility & Time-Horizon Subsystem
        goal_report = calculate_goal_feasibility(
            goals=goals,
            user_investment_capacity=profile.monthly_investment_capacity,
        )

        return ComprehensiveFinancialAnalysisResponse(
            user_id=user_id,
            currency="INR",
            financial_health=health_metrics,
            risk_assessment=risk_result,
            asset_allocation=allocation_breakdown,
            goal_analysis=goal_report,
        )
