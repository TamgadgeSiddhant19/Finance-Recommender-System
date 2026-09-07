from decimal import Decimal
from typing import Union
from app.models.financial_profile import FinancialProfile
from app.schemas.enums import InvestmentExperience, RiskTolerance
from app.schemas.financial_engine import RiskAssessmentResult
from app.schemas.financial_profile import FinancialProfileBase


def calculate_risk_assessment(profile: Union[FinancialProfileBase, FinancialProfile]) -> RiskAssessmentResult:
    """
    Multi-factor deterministic risk profiling algorithm:
    1. Subjective Risk Tolerance (40%)
    2. Investment Experience (20%)
    3. Age-based Risk Horizon Capacity (20%)
    4. Financial Buffer / Runway Capacity (20%)
    5. Debt-to-Income Penalty
    """
    # 1. Subjective Risk Tolerance Score (S1)
    tolerance_map = {
        RiskTolerance.conservative: 25.0,
        RiskTolerance.moderate: 50.0,
        RiskTolerance.aggressive: 75.0,
        RiskTolerance.very_aggressive: 95.0,
    }
    s1_tolerance = tolerance_map.get(profile.risk_tolerance, 50.0)

    # 2. Investment Experience Score (S2)
    experience_map = {
        InvestmentExperience.beginner: 20.0,
        InvestmentExperience.intermediate: 60.0,
        InvestmentExperience.advanced: 90.0,
    }
    s2_experience = experience_map.get(profile.investment_experience, 50.0)

    # 3. Age-based Capacity Score (S3)
    # Younger investors have higher multi-decade recovery horizons
    if profile.age <= 25:
        s3_age = 90.0
    elif profile.age >= 65:
        s3_age = 20.0
    else:
        # Scale smoothly between age 25 (90 pts) and 65 (20 pts)
        s3_age = 90.0 - ((profile.age - 25) * (70.0 / 40.0))

    # 4. Financial Buffer / Emergency Runway Score (S4)
    if profile.monthly_expenses > Decimal("0.00"):
        runway_months = float(profile.total_savings / profile.monthly_expenses)
    else:
        runway_months = 12.0

    if runway_months < 3.0:
        s4_cushion = 25.0
    elif runway_months < 6.0:
        s4_cushion = 50.0
    elif runway_months <= 12.0:
        s4_cushion = 80.0
    else:
        s4_cushion = 95.0

    # 5. Debt Burden Penalty (P)
    annual_income = float(profile.monthly_income * Decimal("12.00"))
    debt = float(profile.total_debt)
    dti = (debt / annual_income) if annual_income > 0 else 0.0

    penalty = 0.0
    if dti > 3.0:
        penalty = 15.0
    elif dti > 1.5:
        penalty = 10.0
    elif dti > 0.5:
        penalty = 5.0

    # Weighted Composite Score
    raw_score = (0.40 * s1_tolerance) + (0.20 * s2_experience) + (0.20 * s3_age) + (0.20 * s4_cushion) - penalty
    final_score = max(0, min(100, int(round(raw_score))))

    # Deterministic Category Thresholds
    if final_score <= 35:
        risk_category = "CONSERVATIVE"
    elif final_score <= 65:
        risk_category = "MODERATE"
    elif final_score <= 85:
        risk_category = "AGGRESSIVE"
    else:
        risk_category = "VERY_AGGRESSIVE"

    score_breakdown = {
        "tolerance_component": round(s1_tolerance, 1),
        "experience_component": round(s2_experience, 1),
        "age_capacity_component": round(s3_age, 1),
        "financial_cushion_component": round(s4_cushion, 1),
        "debt_burden_penalty": round(penalty, 1),
        "raw_weighted_score": round(raw_score, 2),
    }

    return RiskAssessmentResult(
        risk_score=final_score,
        risk_category=risk_category,
        stated_tolerance=profile.risk_tolerance,
        investment_experience=profile.investment_experience,
        age=profile.age,
        score_breakdown=score_breakdown,
    )
