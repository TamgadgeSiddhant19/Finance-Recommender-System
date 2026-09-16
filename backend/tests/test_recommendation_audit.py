"""
Comprehensive tests for Phase 7.4 — Recommendation Explainability & Audit Trail.
Tests deterministic explainability generation, immutable audit log persistence,
input snapshot SHA-256 hashing, decision trace completeness, exclusion taxonomy,
cross-user isolation, and zero-PII compliance.
"""

from decimal import Decimal
import hashlib
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.security import create_access_token
from app.financial_data.models import FinancialProduct
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.recommendations.audit import RecommendationAudit, compute_input_snapshot_hash
from app.recommendations.constants import (
    AUDIT_SCHEMA_VERSION,
    EXCLUSION_TYPE_HARD_REJECT,
    EXCLUSION_TYPE_RANKED_LOWER,
    RECOMMENDATION_ENGINE_VERSION,
    RECOMMENDATION_POLICY_VERSION,
)
from app.recommendations.service import RecommendationService
from app.financial_data.schemas import (
    AssetClass,
    ProductRiskLevel as RiskLevel,
    ProductType,
)
from app.schemas.enums import (
    GoalType,
    InvestmentExperience,
    Priority,
    RiskTolerance,
)
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase


def make_auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def get_mock_products():
    return [
        FinancialProduct(
            id=1,
            symbol="NIFTY50-INDX",
            name="Nifty 50 Index Fund",
            product_type=ProductType.index_fund,
            asset_class=AssetClass.equity,
            issuer="UTI Mutual Fund",
            currency="INR",
            country="India",
            risk_level=RiskLevel.high,
            expense_ratio=Decimal("0.0020"),
            minimum_investment=Decimal("500.00"),
        ),
        FinancialProduct(
            id=2,
            symbol="MIDCAP-EQ",
            name="Motilal Oswal Midcap 150 Index Fund",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.equity,
            issuer="Motilal Oswal AMC",
            currency="INR",
            country="India",
            risk_level=RiskLevel.very_high,
            expense_ratio=Decimal("0.0030"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=3,
            symbol="BHARAT-BOND",
            name="Edelweiss Bharat Bond ETF - April 2030",
            product_type=ProductType.bond,
            asset_class=AssetClass.debt,
            issuer="Edelweiss AMC",
            currency="INR",
            country="India",
            risk_level=RiskLevel.low,
            expense_ratio=Decimal("0.0005"),
            minimum_investment=Decimal("1000.00"),
        ),
        FinancialProduct(
            id=4,
            symbol="GOLD-BEES",
            name="Nippon India ETF Gold BeES",
            product_type=ProductType.etf,
            asset_class=AssetClass.gold,
            issuer="Nippon AMC",
            currency="INR",
            country="India",
            risk_level=RiskLevel.moderate,
            expense_ratio=Decimal("0.0010"),
            minimum_investment=Decimal("100.00"),
        ),
        FinancialProduct(
            id=5,
            symbol="LIQUID-CSH",
            name="HDFC Liquid Fund Direct Plan Growth",
            product_type=ProductType.mutual_fund,
            asset_class=AssetClass.cash,
            issuer="HDFC AMC",
            currency="INR",
            country="India",
            risk_level=RiskLevel.low,
            expense_ratio=Decimal("0.0020"),
            minimum_investment=Decimal("500.00"),
        ),
    ]


def test_input_snapshot_hash_stability():
    """Verifies that identical inputs produce identical SHA-256 hashes, and mutations change hash."""
    profile_1 = FinancialProfileBase(
        age=30,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("50000.00"),
        monthly_investment_capacity=Decimal("30000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
        total_savings=Decimal("300000.00"),
        emergency_fund_current=Decimal("200000.00"),
        total_debt=Decimal("0.00"),
    )
    goals_1 = [
        FinancialGoalBase(
            goal_type=GoalType.retirement,
            target_amount=Decimal("5000000.00"),
            target_years=10,
            priority=Priority.high,
        )
    ]

    hash_1 = compute_input_snapshot_hash(profile_1, goals_1)
    assert len(hash_1) == 64
    assert all(c in "0123456789abcdef" for c in hash_1)

    # Identical profile and goals must yield exact same hash
    hash_1_duplicate = compute_input_snapshot_hash(profile_1, goals_1)
    assert hash_1 == hash_1_duplicate

    # Modified income must yield different hash
    profile_mod = profile_1.model_copy(update={"monthly_income": Decimal("120000.00")})
    hash_mod = compute_input_snapshot_hash(profile_mod, goals_1)
    assert hash_1 != hash_mod

    # Modified goal target must yield different hash
    goals_mod = [
        FinancialGoalBase(
            goal_type=GoalType.retirement,
            target_amount=Decimal("6000000.00"),
            target_years=10,
            priority=Priority.high,
        )
    ]
    hash_goal_mod = compute_input_snapshot_hash(profile_1, goals_mod)
    assert hash_1 != hash_goal_mod


def test_stateless_recommendation_explainability_and_trace():
    """Verifies structured explanation, exclusion taxonomy, and decision trace on generate_recommendation."""
    profile = FinancialProfileBase(
        age=28,
        monthly_income=Decimal("120000.00"),
        monthly_expenses=Decimal("60000.00"),
        monthly_investment_capacity=Decimal("40000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
        total_savings=Decimal("400000.00"),
        emergency_fund_current=Decimal("300000.00"),
        total_debt=Decimal("0.00"),
    )
    goals = [
        FinancialGoalBase(
            goal_type=GoalType.wealth_creation,
            target_amount=Decimal("3000000.00"),
            target_years=7,
            priority=Priority.high,
        )
    ]
    products = get_mock_products()

    rec = RecommendationService.generate_recommendation(
        profile=profile,
        goals=goals,
        available_products=products,
    )

    # 1. Versioning
    assert rec.engine_version == RECOMMENDATION_ENGINE_VERSION
    assert rec.policy_version == RECOMMENDATION_POLICY_VERSION
    assert len(rec.input_snapshot_hash) == 64

    # 2. Explanation Object
    assert rec.explanation is not None
    assert rec.explanation.engine_version == RECOMMENDATION_ENGINE_VERSION
    assert rec.explanation.policy_version == RECOMMENDATION_POLICY_VERSION
    assert "deterministic" in rec.explanation.summary.lower()

    # Risk Explanation
    assert rec.explanation.risk_explanation.risk_category == rec.risk_category
    assert rec.explanation.risk_explanation.risk_score == rec.risk_score
    assert len(rec.explanation.risk_explanation.factors) >= 4

    # Goal Explanation
    assert rec.explanation.goal_explanation is not None
    assert rec.explanation.goal_explanation.nominal_target == Decimal("3000000.00")
    assert rec.explanation.goal_explanation.inflation_adjusted_target > Decimal("3000000.00")
    assert rec.explanation.goal_explanation.feasibility_status in ("ON_TRACK", "MODERATELY_UNDERFUNDED", "SIGNIFICANTLY_UNDERFUNDED", "NOT_FEASIBLE")

    # Allocation Explanation
    assert len(rec.explanation.allocation_explanation) >= 2
    for item in rec.explanation.allocation_explanation:
        assert item.asset_class in ("equity", "debt", "gold", "cash")
        assert item.allocation_percentage > Decimal("0.00")
        assert item.sip_amount > Decimal("0.00")
        assert len(item.policy_rule) > 0

    # Selected Products Explanations
    assert len(rec.explanation.selected_products) == len(rec.portfolio_items)
    for sel in rec.explanation.selected_products:
        assert len(sel.selection_reasons) >= 3
        assert any("✓" in r for r in sel.selection_reasons)

    # Exclusion Taxonomy
    assert len(rec.explanation.excluded_products) > 0
    exclusion_types = {ex.exclusion_type for ex in rec.explanation.excluded_products}
    assert EXCLUSION_TYPE_HARD_REJECT in exclusion_types or EXCLUSION_TYPE_RANKED_LOWER in exclusion_types

    # Decision Trace
    assert rec.decision_trace is not None
    assert rec.decision_trace.engine_version == RECOMMENDATION_ENGINE_VERSION
    assert rec.decision_trace.input_snapshot_hash == rec.input_snapshot_hash
    assert rec.decision_trace.profile_snapshot["monthly_investment_capacity"] == 40000.0
    assert rec.decision_trace.risk_assessment["risk_score"] == rec.risk_score
    assert len(rec.decision_trace.selected_products) == len(rec.portfolio_items)
    assert rec.decision_trace.validation_report["is_valid"] is True


@pytest.mark.asyncio
async def test_recommendation_audit_persistence_and_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Verifies end-to-end audit log creation in DB and retrieval via /me/latest/audit and /{rec_id}/audit."""
    # 1. Seed Products
    for p in get_mock_products():
        db_session.add(p)

    # 2. Seed User
    user = User(email="audit_tester@example.com", password_hash="dummy_hashed_pw")
    db_session.add(user)
    await db_session.flush()

    # 3. Seed Profile
    profile = FinancialProfile(
        user_id=user.id,
        age=32,
        monthly_income=Decimal("150000.00"),
        monthly_expenses=Decimal("70000.00"),
        total_savings=Decimal("600000.00"),
        monthly_investment_capacity=Decimal("50000.00"),
        total_debt=Decimal("0.00"),
        risk_tolerance=RiskTolerance.aggressive,
        investment_experience=InvestmentExperience.advanced,
    )
    db_session.add(profile)

    # 4. Seed Goal
    goal = FinancialGoal(
        user_id=user.id,
        goal_type=GoalType.retirement,
        target_amount=Decimal("15000000.00"),
        target_years=15,
        priority=Priority.high,
    )
    db_session.add(goal)
    await db_session.commit()

    headers = make_auth_headers(user.id)

    # 5. Generate Recommendation
    gen_res = await client.post(f"/api/v1/recommendations/{user.id}", headers=headers)
    assert gen_res.status_code == 201
    rec_data = gen_res.json()
    rec_id = rec_data["recommendation_id"]
    assert rec_id is not None
    assert rec_data["engine_version"] == RECOMMENDATION_ENGINE_VERSION
    assert rec_data["policy_version"] == RECOMMENDATION_POLICY_VERSION
    assert len(rec_data["input_snapshot_hash"]) == 64
    assert rec_data["explanation"] is not None

    # 6. Verify RecommendationAudit record exists in database
    audit_stmt = select(RecommendationAudit).where(
        RecommendationAudit.recommendation_id == rec_id,
        RecommendationAudit.user_id == user.id,
    )
    audit_res = await db_session.execute(audit_stmt)
    db_audit = audit_res.scalar_one_or_none()
    assert db_audit is not None
    assert db_audit.engine_version == RECOMMENDATION_ENGINE_VERSION
    assert db_audit.policy_version == RECOMMENDATION_POLICY_VERSION
    assert db_audit.schema_version == AUDIT_SCHEMA_VERSION
    assert db_audit.input_snapshot_hash == rec_data["input_snapshot_hash"]

    # 7. Query GET /api/v1/recommendations/me/latest/audit
    latest_audit_res = await client.get("/api/v1/recommendations/me/latest/audit", headers=headers)
    assert latest_audit_res.status_code == 200
    latest_audit = latest_audit_res.json()
    assert latest_audit["recommendation_id"] == rec_id
    assert latest_audit["engine_version"] == RECOMMENDATION_ENGINE_VERSION
    assert latest_audit["schema_version"] == AUDIT_SCHEMA_VERSION
    assert latest_audit["input_snapshot_hash"] == rec_data["input_snapshot_hash"]
    assert latest_audit["decision_trace"] is not None
    assert latest_audit["decision_trace"]["profile_snapshot"]["monthly_income"] == 150000.0
    assert len(latest_audit["decision_trace"]["selected_products"]) > 0

    # 8. Query GET /api/v1/recommendations/{rec_id}/audit
    id_audit_res = await client.get(f"/api/v1/recommendations/{rec_id}/audit", headers=headers)
    assert id_audit_res.status_code == 200
    id_audit = id_audit_res.json()
    assert id_audit["id"] == db_audit.id
    assert id_audit["recommendation_id"] == rec_id


@pytest.mark.asyncio
async def test_cross_user_audit_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Verifies that User B cannot access User A's recommendation audit trail."""
    # Seed Product
    for p in get_mock_products():
        db_session.add(p)

    # Seed User A
    user_a = User(email="user_a@example.com", password_hash="hash_a")
    db_session.add(user_a)
    await db_session.flush()

    prof_a = FinancialProfile(
        user_id=user_a.id,
        age=30,
        monthly_income=Decimal("80000.00"),
        monthly_expenses=Decimal("40000.00"),
        total_savings=Decimal("100000.00"),
        monthly_investment_capacity=Decimal("20000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    db_session.add(prof_a)

    # Seed User B
    user_b = User(email="user_b@example.com", password_hash="hash_b")
    db_session.add(user_b)
    await db_session.flush()

    prof_b = FinancialProfile(
        user_id=user_b.id,
        age=35,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("200000.00"),
        monthly_investment_capacity=Decimal("30000.00"),
        risk_tolerance=RiskTolerance.aggressive,
        investment_experience=InvestmentExperience.advanced,
    )
    db_session.add(prof_b)
    await db_session.commit()

    # Generate recommendation for User A
    headers_a = make_auth_headers(user_a.id)
    gen_res = await client.post(f"/api/v1/recommendations/{user_a.id}", headers=headers_a)
    assert gen_res.status_code == 201
    rec_a_id = gen_res.json()["recommendation_id"]

    # User B attempts to access User A's audit
    headers_b = make_auth_headers(user_b.id)
    forbidden_audit_res = await client.get(f"/api/v1/recommendations/{rec_a_id}/audit", headers=headers_b)
    assert forbidden_audit_res.status_code in (403, 404)


def test_zero_pii_in_audit_trace():
    """Verifies that sensitive credentials, passwords, tokens are not leaked into decision trace or snapshots."""
    profile = FinancialProfileBase(
        age=30,
        monthly_income=Decimal("100000.00"),
        monthly_expenses=Decimal("50000.00"),
        total_savings=Decimal("300000.00"),
        monthly_investment_capacity=Decimal("30000.00"),
        risk_tolerance=RiskTolerance.moderate,
        investment_experience=InvestmentExperience.intermediate,
    )
    products = get_mock_products()
    rec = RecommendationService.generate_recommendation(
        profile=profile,
        available_products=products,
    )

    trace_json = json.dumps(rec.decision_trace.model_dump(mode="json"))
    for sensitive in ("password", "password_hash", "access_token", "secret", "api_key"):
        assert sensitive not in trace_json.lower()
