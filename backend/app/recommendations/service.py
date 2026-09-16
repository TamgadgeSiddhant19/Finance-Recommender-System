from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.financial_data.models import FinancialProduct
from app.financial_data.repository import FinancialProductRepository
from app.financial_data.schemas import FinancialProductResponse

from app.goals.calculator import calculate_complete_goal_projection, quantize_dec
from app.market.schemas import HistoricalCandle
from app.market.service import get_market_data_service
from app.models.financial_goal import FinancialGoal
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.recommendations.allocation import (
    determine_primary_horizon,
    generate_goal_aware_allocation_with_reasons,
    generate_target_allocation,
)
from app.recommendations.filters import filter_eligible_products
from app.recommendations.models import Recommendation, RecommendationItem
from app.recommendations.policy import (
    GoalHorizonBucket,
    classify_horizon_bucket,
    generate_funding_gap_actions,
)
from app.recommendations.portfolio import construct_portfolio
from app.recommendations.product_intelligence import build_product_intelligence
from app.recommendations.schemas import (
    GoalRecommendationSummary,
    PortfolioValidationReport,
    ProductExclusionSummary,
    ProductSelectionReason,
    RecommendationHistoryItem,
    RecommendationResponse,
    RecommendedPortfolioItem,
    TargetAllocationSummary,
)
from app.recommendations.scoring import score_product
from app.recommendations.validators import validate_portfolio
from app.schemas.enums import Priority
from app.schemas.financial_goal import FinancialGoalBase
from app.schemas.financial_profile import FinancialProfileBase
from app.services.risk_scoring import calculate_risk_assessment

ProductTypeUnion = Union[FinancialProduct, FinancialProductResponse]
GoalTypeUnion = Union[FinancialGoal, FinancialGoalBase]
ProfileTypeUnion = Union[FinancialProfile, FinancialProfileBase]


class RecommendationService:
    """
    Deterministic Financial Recommendation Engine orchestrator:
    Combines profile data, risk profile, goal time-horizons, Phase 7.1 mathematical projections,
    Phase 7.2 goal-aware allocation policies, and Phase 7.3 product intelligence metrics.
    """

    @classmethod
    def generate_recommendation(
        cls,
        profile: ProfileTypeUnion,
        goals: Sequence[GoalTypeUnion] = (),
        available_products: Sequence[ProductTypeUnion] = (),
        user_id: Optional[int] = None,
        product_market_candles: Optional[Dict[str, List[HistoricalCandle]]] = None,
    ) -> RecommendationResponse:
        """
        Pure deterministic recommendation generator (Stateless).
        """
        # 1. Deterministic Multi-factor Risk Scoring
        risk_result = calculate_risk_assessment(profile)
        risk_category = risk_result.risk_category
        risk_score = risk_result.risk_score
        monthly_capacity = Decimal(str(profile.monthly_investment_capacity or Decimal("0.00")))
        lump_sum_capacity = Decimal(str(getattr(profile, "emergency_fund_current", Decimal("0.00")) or Decimal("0.00")))

        # 2. Process Goals & Phase 7.1 Mathematical Feasibility Projections
        goals_breakdown: List[GoalRecommendationSummary] = []
        primary_goal_projection = None
        primary_horizon_bucket = GoalHorizonBucket.GENERAL_WEALTH
        funding_gap_actions: List[str] = []

        valid_goals = [g for g in goals if getattr(g, "target_years", 0) and g.target_years > 0]

        if valid_goals:
            priority_weights = {
                Priority.high: 3,
                "high": 3,
                Priority.medium: 2,
                "medium": 2,
                Priority.low: 1,
                "low": 1,
            }

            def goal_sort_key(g: GoalTypeUnion):
                p_val = priority_weights.get(getattr(g, "priority", Priority.medium), 2)
                return (-p_val, g.target_years)

            sorted_goals = sorted(valid_goals, key=goal_sort_key)
            primary_goal = sorted_goals[0]
            _, primary_horizon_bucket = determine_primary_horizon(sorted_goals)

            # Distribute monthly investment capacity across goals respecting priority
            remaining_capacity = monthly_capacity
            for g in sorted_goals:
                g_target = Decimal(str(g.target_amount))
                g_current = Decimal(str(getattr(g, "current_amount", Decimal("0.00")) or Decimal("0.00")))
                g_years = int(g.target_years)
                g_type_val = g.goal_type.value if hasattr(g.goal_type, "value") else str(g.goal_type)
                g_priority_val = g.priority.value if hasattr(g.priority, "value") else str(g.priority)

                # Preliminary calculation to check required SIP
                prelim_proj = calculate_complete_goal_projection(
                    target_amount=g_target,
                    current_amount=g_current,
                    horizon_years=g_years,
                    monthly_contribution=Decimal("0.00"),
                )

                allocated_sip = min(remaining_capacity, prelim_proj.required_monthly_contribution)
                if allocated_sip <= Decimal("0.00") and remaining_capacity > Decimal("0.00"):
                    allocated_sip = remaining_capacity
                remaining_capacity = max(Decimal("0.00"), remaining_capacity - allocated_sip)

                proj = calculate_complete_goal_projection(
                    target_amount=g_target,
                    current_amount=g_current,
                    horizon_years=g_years,
                    monthly_contribution=allocated_sip,
                    goal_id=getattr(g, "id", None),
                    goal_type=getattr(g, "goal_type", "retirement"),
                )

                h_bucket = classify_horizon_bucket(g_years)
                g_actions = generate_funding_gap_actions(
                    feasibility_status=proj.feasibility_status.value,
                    required_sip=proj.required_monthly_contribution,
                    current_sip=allocated_sip,
                    shortfall=proj.projected_shortfall_or_surplus,
                    horizon_years=g_years,
                )

                g_summary = GoalRecommendationSummary(
                    goal_id=getattr(g, "id", None),
                    goal_type=g_type_val,
                    target_amount=quantize_dec(g_target, 2),
                    current_amount=quantize_dec(g_current, 2),
                    target_years=g_years,
                    priority=g_priority_val,
                    feasibility_status=proj.feasibility_status.value,
                    funding_ratio_pct=proj.funding_ratio_pct,
                    projected_corpus=proj.projected_corpus,
                    inflation_adjusted_target=proj.inflation_adjusted_target,
                    shortfall_or_surplus=proj.projected_shortfall_or_surplus,
                    allocated_monthly_sip=quantize_dec(allocated_sip, 2),
                    required_monthly_sip=proj.required_monthly_contribution,
                    horizon_bucket=h_bucket.value,
                    funding_gap_actions=g_actions,
                )
                goals_breakdown.append(g_summary)

                if g == primary_goal:
                    primary_goal_projection = proj
                    funding_gap_actions = g_actions

        # 3. Goal-Aware Target Asset Allocation & Rationale
        target_alloc, allocation_reasons, horizon_bucket = generate_goal_aware_allocation_with_reasons(
            risk_category=risk_category,
            goals=valid_goals,
        )

        # 4. Product Eligibility Filtering
        eligible_products, raw_exclusions = filter_eligible_products(
            products=available_products,
            risk_category=risk_category,
            investment_capacity=monthly_capacity,
        )

        eligible_ids = {p.id for p in eligible_products}
        excluded_products: List[ProductExclusionSummary] = [
            ProductExclusionSummary(
                product_id=ex.get("product_id"),
                symbol=ex.get("symbol", ""),
                name=ex.get("name", ""),
                reason=ex.get("reason", "Filtered by suitability constraints"),
                category="Risk Limit" if "risk" in ex.get("reason", "").lower() else "Capacity Constraint",
            )
            for ex in raw_exclusions
        ]

        # 5. Deterministic Product Scoring & Product Intelligence
        target_dict = {
            "equity": target_alloc.equity_pct,
            "debt": target_alloc.debt_pct,
            "gold": target_alloc.gold_pct,
            "cash": target_alloc.cash_pct,
        }

        candle_map = product_market_candles or {}
        scored_products: List[tuple] = []

        for prod in eligible_products:
            prod_candles = candle_map.get(prod.symbol) or candle_map.get(prod.symbol.upper()) or []
            intel = build_product_intelligence(
                product=prod,
                user_risk_cat=risk_category,
                monthly_capacity=monthly_capacity,
                goals=valid_goals,
                candles=prod_candles,
            )
            score, reasons, _ = score_product(
                product=prod,
                user_risk_cat=risk_category,
                monthly_capacity=monthly_capacity,
                target_allocation_dict=target_dict,
                goals=valid_goals,
                intelligence_report=intel,
            )
            scored_products.append((prod, score, reasons, intel))

        # 6. Candidate Portfolio Construction
        portfolio_items = construct_portfolio(
            scored_products=scored_products,
            target_allocation=target_alloc,
            monthly_capacity=monthly_capacity,
            lump_sum_capacity=Decimal("0.00"),
        )

        # 7. Portfolio Validation
        validation_report = validate_portfolio(
            portfolio_items=portfolio_items,
            target_allocation=target_alloc,
            monthly_capacity=monthly_capacity,
            risk_category=risk_category,
            eligible_product_ids=eligible_ids,
        )

        total_sip = sum((item.suggested_monthly_sip for item in portfolio_items), Decimal("0.00"))
        total_lump_sum = sum((item.suggested_lump_sum for item in portfolio_items), Decimal("0.00"))

        # 8. Assemble goal-aware summary metrics
        goal_status_str = primary_goal_projection.feasibility_status.value if primary_goal_projection else None
        nominal_target_val = primary_goal_projection.target_amount if primary_goal_projection else None
        inflated_target_val = primary_goal_projection.inflation_adjusted_target if primary_goal_projection else None
        proj_corpus_val = primary_goal_projection.projected_corpus if primary_goal_projection else None
        funding_ratio_val = primary_goal_projection.funding_ratio_pct if primary_goal_projection else None
        shortfall_surplus_val = primary_goal_projection.projected_shortfall_or_surplus if primary_goal_projection else None

        return RecommendationResponse(
            recommendation_id=None,
            user_id=user_id,
            risk_category=risk_category,
            risk_score=risk_score,
            monthly_investment_capacity=monthly_capacity,
            target_allocation=target_alloc,
            portfolio_items=portfolio_items,
            total_monthly_sip=total_sip,
            total_lump_sum=total_lump_sum,
            validation_report=validation_report,
            goal_horizon_bucket=horizon_bucket.value,
            goal_feasibility_status=goal_status_str,
            nominal_target=nominal_target_val,
            inflation_adjusted_target=inflated_target_val,
            projected_corpus=proj_corpus_val,
            funding_ratio=funding_ratio_val,
            goal_shortfall_or_surplus=shortfall_surplus_val,
            goal_aware_allocation=target_alloc,
            allocation_reasons=allocation_reasons,
            funding_gap_actions=funding_gap_actions,
            goals_breakdown=goals_breakdown,
            excluded_products=excluded_products,
        )

    @classmethod
    async def generate_and_save_for_user(
        cls,
        db: AsyncSession,
        user_id: int,
    ) -> RecommendationResponse:
        """
        Loads user, profile, goals, and products from database,
        queries MarketDataService for real/historical candles,
        computes recommendation with product intelligence, persists record, and returns response.
        """
        # 1. Fetch User
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        # 2. Fetch Profile
        profile_res = await db.execute(
            select(FinancialProfile).where(FinancialProfile.user_id == user_id)
        )
        profile = profile_res.scalar_one_or_none()
        if not profile:
            raise ValueError(f"Financial profile not found for user {user_id}.")

        # 3. Fetch Goals
        goals_res = await db.execute(
            select(FinancialGoal).where(FinancialGoal.user_id == user_id).order_by(FinancialGoal.created_at.desc())
        )
        goals = list(goals_res.scalars().all())

        # 4. Fetch Products Catalog
        products_res = await db.execute(select(FinancialProduct))
        products = list(products_res.scalars().all())

        # 5. Fetch available market candle history via MarketDataService
        market_service = get_market_data_service()
        candle_map: Dict[str, List[HistoricalCandle]] = {}
        for p in products:
            try:
                candles = await market_service.get_historical_candles(p.symbol)
                if candles:
                    candle_map[p.symbol] = candles
            except Exception:
                pass

        # 6. Generate Recommendation with Product Intelligence
        rec_resp = cls.generate_recommendation(
            profile=profile,
            goals=goals,
            available_products=products,
            user_id=user_id,
            product_market_candles=candle_map,
        )

        # 7. Build goal metadata json for audit and detail views
        goal_metadata = {
            "nominal_target": float(rec_resp.nominal_target) if rec_resp.nominal_target is not None else None,
            "inflation_adjusted_target": float(rec_resp.inflation_adjusted_target) if rec_resp.inflation_adjusted_target is not None else None,
            "projected_corpus": float(rec_resp.projected_corpus) if rec_resp.projected_corpus is not None else None,
            "funding_ratio": float(rec_resp.funding_ratio) if rec_resp.funding_ratio is not None else None,
            "goal_shortfall_or_surplus": float(rec_resp.goal_shortfall_or_surplus) if rec_resp.goal_shortfall_or_surplus is not None else None,
            "allocation_reasons": rec_resp.allocation_reasons,
            "funding_gap_actions": rec_resp.funding_gap_actions,
            "goals_breakdown": [g.model_dump(mode="json") for g in rec_resp.goals_breakdown],
            "excluded_products": [ex.model_dump(mode="json") for ex in rec_resp.excluded_products],
        }

        # 8. Persist Recommendation to Database
        db_rec = Recommendation(
            user_id=user_id,
            risk_category=rec_resp.risk_category,
            risk_score=rec_resp.risk_score,
            monthly_capacity=rec_resp.monthly_investment_capacity,
            target_equity_pct=rec_resp.target_allocation.equity_pct,
            target_debt_pct=rec_resp.target_allocation.debt_pct,
            target_gold_pct=rec_resp.target_allocation.gold_pct,
            target_cash_pct=rec_resp.target_allocation.cash_pct,
            total_monthly_sip=rec_resp.total_monthly_sip,
            total_lump_sum=rec_resp.total_lump_sum,
            is_valid=rec_resp.validation_report.is_valid,
            validation_details=rec_resp.validation_report.model_dump(mode="json"),
            goal_horizon_bucket=rec_resp.goal_horizon_bucket,
            goal_feasibility_status=rec_resp.goal_feasibility_status,
            goal_metadata=goal_metadata,
        )
        db.add(db_rec)
        await db.flush()  # Populates db_rec.id

        for item in rec_resp.portfolio_items:
            reasons_json = [r.model_dump(mode="json") for r in item.selection_reasons]
            intel_meta = {
                "risk_compatibility_score": float(item.risk_compatibility_score) if item.risk_compatibility_score is not None else None,
                "goal_compatibility_score": float(item.goal_compatibility_score) if item.goal_compatibility_score is not None else None,
                "horizon_compatibility_score": float(item.horizon_compatibility_score) if item.horizon_compatibility_score is not None else None,
                "historical_return_1y": float(item.historical_return_1y) if item.historical_return_1y is not None else None,
                "historical_return_3y": float(item.historical_return_3y) if item.historical_return_3y is not None else None,
                "historical_return_5y": float(item.historical_return_5y) if item.historical_return_5y is not None else None,
                "volatility": float(item.volatility) if item.volatility is not None else None,
                "max_drawdown": float(item.max_drawdown) if item.max_drawdown is not None else None,
                "current_drawdown": float(item.current_drawdown) if item.current_drawdown is not None else None,
                "expense_ratio": float(item.expense_ratio) if item.expense_ratio is not None else None,
                "data_quality_score": float(item.data_quality_score) if item.data_quality_score is not None else None,
                "data_source": item.data_source,
                "data_status": item.data_status,
                "data_as_of": item.data_as_of.isoformat() if item.data_as_of else None,
            }

            db_item = RecommendationItem(
                recommendation_id=db_rec.id,
                financial_product_id=item.product_id,
                symbol=item.symbol,
                name=item.name,
                product_type=item.product_type.value if hasattr(item.product_type, "value") else str(item.product_type),
                asset_class=item.asset_class.value if hasattr(item.asset_class, "value") else str(item.asset_class),
                risk_level=item.risk_level.value if hasattr(item.risk_level, "value") else str(item.risk_level),
                suitability_score=item.suitability_score,
                allocation_percentage=item.allocation_percentage,
                monthly_sip_amount=item.suggested_monthly_sip,
                lump_sum_amount=item.suggested_lump_sum,
                selection_reasons=reasons_json,
                intelligence_metadata=intel_meta,
            )
            db.add(db_item)

        await db.commit()
        await db.refresh(db_rec)

        rec_resp.recommendation_id = db_rec.id
        return rec_resp

    @classmethod
    async def get_user_recommendation_history(
        cls,
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[RecommendationHistoryItem]:
        """
        Retrieves list of past recommendations for a user.
        """
        stmt = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        records = res.scalars().all()
        return [RecommendationHistoryItem.model_validate(r) for r in records]

    @classmethod
    async def get_recommendation_by_id(
        cls,
        db: AsyncSession,
        user_id: int,
        recommendation_id: int,
    ) -> Optional[RecommendationResponse]:
        """
        Retrieves full details of a specific stored recommendation including product intelligence features.
        """
        stmt = (
            select(Recommendation)
            .where(Recommendation.id == recommendation_id, Recommendation.user_id == user_id)
            .options(selectinload(Recommendation.items))
        )
        res = await db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            return None

        portfolio_items: List[RecommendedPortfolioItem] = []
        for it in rec.items:
            reasons = [ProductSelectionReason(**r) for r in (it.selection_reasons or [])]
            imeta = it.intelligence_metadata or {}
            as_of_dt = datetime.fromisoformat(imeta["data_as_of"]) if imeta.get("data_as_of") else None

            portfolio_items.append(
                RecommendedPortfolioItem(
                    product_id=it.financial_product_id,
                    symbol=it.symbol,
                    name=it.name,
                    product_type=it.product_type,
                    asset_class=it.asset_class,
                    risk_level=it.risk_level,
                    suitability_score=it.suitability_score,
                    allocation_percentage=it.allocation_percentage,
                    suggested_monthly_sip=it.monthly_sip_amount,
                    suggested_lump_sum=it.lump_sum_amount,
                    selection_reasons=reasons,
                    risk_compatibility_score=Decimal(str(imeta["risk_compatibility_score"])) if imeta.get("risk_compatibility_score") is not None else None,
                    goal_compatibility_score=Decimal(str(imeta["goal_compatibility_score"])) if imeta.get("goal_compatibility_score") is not None else None,
                    horizon_compatibility_score=Decimal(str(imeta["horizon_compatibility_score"])) if imeta.get("horizon_compatibility_score") is not None else None,
                    historical_return_1y=Decimal(str(imeta["historical_return_1y"])) if imeta.get("historical_return_1y") is not None else None,
                    historical_return_3y=Decimal(str(imeta["historical_return_3y"])) if imeta.get("historical_return_3y") is not None else None,
                    historical_return_5y=Decimal(str(imeta["historical_return_5y"])) if imeta.get("historical_return_5y") is not None else None,
                    volatility=Decimal(str(imeta["volatility"])) if imeta.get("volatility") is not None else None,
                    max_drawdown=Decimal(str(imeta["max_drawdown"])) if imeta.get("max_drawdown") is not None else None,
                    current_drawdown=Decimal(str(imeta["current_drawdown"])) if imeta.get("current_drawdown") is not None else None,
                    expense_ratio=Decimal(str(imeta["expense_ratio"])) if imeta.get("expense_ratio") is not None else None,
                    data_quality_score=Decimal(str(imeta["data_quality_score"])) if imeta.get("data_quality_score") is not None else None,
                    data_source=imeta.get("data_source", "master_catalog"),
                    data_status=imeta.get("data_status", "unavailable"),
                    data_as_of=as_of_dt,
                )
            )

        target_alloc = TargetAllocationSummary(
            equity_pct=rec.target_equity_pct,
            debt_pct=rec.target_debt_pct,
            gold_pct=rec.target_gold_pct,
            cash_pct=rec.target_cash_pct,
        )

        validation_report = rec.validation_details or {"is_valid": rec.is_valid, "checks": []}
        meta = rec.goal_metadata or {}

        goals_breakdown = [GoalRecommendationSummary(**g) for g in meta.get("goals_breakdown", [])]
        excluded_products = [ProductExclusionSummary(**ex) for ex in meta.get("excluded_products", [])]

        return RecommendationResponse(
            recommendation_id=rec.id,
            user_id=rec.user_id,
            risk_category=rec.risk_category,
            risk_score=rec.risk_score,
            monthly_investment_capacity=rec.monthly_capacity,
            target_allocation=target_alloc,
            portfolio_items=portfolio_items,
            total_monthly_sip=rec.total_monthly_sip,
            total_lump_sum=rec.total_lump_sum,
            validation_report=validation_report,
            created_at=rec.created_at,
            goal_horizon_bucket=rec.goal_horizon_bucket or "GENERAL_WEALTH",
            goal_feasibility_status=rec.goal_feasibility_status,
            nominal_target=Decimal(str(meta["nominal_target"])) if meta.get("nominal_target") is not None else None,
            inflation_adjusted_target=Decimal(str(meta["inflation_adjusted_target"])) if meta.get("inflation_adjusted_target") is not None else None,
            projected_corpus=Decimal(str(meta["projected_corpus"])) if meta.get("projected_corpus") is not None else None,
            funding_ratio=Decimal(str(meta["funding_ratio"])) if meta.get("funding_ratio") is not None else None,
            goal_shortfall_or_surplus=Decimal(str(meta["goal_shortfall_or_surplus"])) if meta.get("goal_shortfall_or_surplus") is not None else None,
            goal_aware_allocation=target_alloc,
            allocation_reasons=meta.get("allocation_reasons"),
            funding_gap_actions=meta.get("funding_gap_actions", []),
            goals_breakdown=goals_breakdown,
            excluded_products=excluded_products,
        )

    @staticmethod
    def prepare_rag_explanation_payload(
        rec: RecommendationResponse,
        profile: ProfileTypeUnion,
        goals: Sequence[GoalTypeUnion] = (),
    ) -> Dict[str, Any]:
        """
        Builds a structured contextual payload for downstream RAG / Gemini synthesis.
        Ensures strict separation: deterministic engine provides all numbers and facts,
        while the downstream LLM only provides natural-language narrative synthesis.
        """
        return {
            "user_context": {
                "user_id": rec.user_id,
                "risk_profile": rec.risk_category,
                "risk_score": rec.risk_score,
                "monthly_surplus_inr": float(rec.monthly_investment_capacity),
                "goal_horizon_bucket": rec.goal_horizon_bucket,
                "goal_feasibility_status": rec.goal_feasibility_status,
            },
            "deterministic_target_allocation": {
                "equity_pct": float(rec.target_allocation.equity_pct),
                "debt_pct": float(rec.target_allocation.debt_pct),
                "gold_pct": float(rec.target_allocation.gold_pct),
                "cash_pct": float(rec.target_allocation.cash_pct),
            },
            "portfolio_instruments": [
                {
                    "symbol": item.symbol,
                    "name": item.name,
                    "asset_class": item.asset_class.value if hasattr(item.asset_class, "value") else str(item.asset_class),
                    "allocation_pct": float(item.allocation_percentage),
                    "monthly_sip_inr": float(item.suggested_monthly_sip),
                    "suitability_score": float(item.suitability_score),
                    "selection_reasons": [r.description for r in item.selection_reasons],
                    "historical_return_1y": float(item.historical_return_1y) if item.historical_return_1y is not None else None,
                    "volatility": float(item.volatility) if item.volatility is not None else None,
                    "max_drawdown": float(item.max_drawdown) if item.max_drawdown is not None else None,
                    "data_source": item.data_source,
                }
                for item in rec.portfolio_items
            ],
            "goal_horizons": [
                {
                    "goal_type": g.goal_type.value if hasattr(g.goal_type, "value") else str(g.goal_type),
                    "target_amount": float(g.target_amount),
                    "target_years": g.target_years,
                }
                for g in goals
            ],
            "allocation_reasons": rec.allocation_reasons,
            "funding_gap_actions": rec.funding_gap_actions,
        }
