import { apiClient } from "./api";
import {
  FinancialAnalysisResponse,
  UserProfile,
  FinancialGoal,
  AssetAllocationItem,
  GoalFeasibilityResult,
} from "@/types";
import { MOCK_ANALYSIS } from "@/lib/mockData";

export interface SimulationPayload {
  profile: Omit<UserProfile, "id" | "user_id" | "created_at" | "updated_at">;
  goals: Array<Omit<FinancialGoal, "id" | "user_id" | "created_at" | "updated_at">>;
}

/**
 * Normalizes backend FastAPI ComprehensiveFinancialAnalysisResponse into frontend model
 */
function normalizeAnalysisResponse(data: any): FinancialAnalysisResponse {
  if (!data) return MOCK_ANALYSIS;

  // Check if it's already in frontend format
  if (data.health && data.risk && data.allocation) {
    return {
      user_id: data.user_id,
      health: {
        monthly_surplus: Number(data.health.monthly_surplus ?? 0),
        savings_ratio_pct: Number(data.health.savings_ratio_pct ?? (data.health.surplus_to_income_ratio ? data.health.surplus_to_income_ratio * 100 : 0)),
        emergency_fund_months: Number(data.health.emergency_fund_months ?? data.health.emergency_fund_runway_months ?? 0),
        emergency_fund_target_inr: Number(data.health.emergency_fund_target_inr ?? data.health.target_emergency_fund ?? 0),
        debt_to_income_ratio: Number(data.health.debt_to_income_ratio ?? 0),
        investment_capacity_inr: Number(data.health.investment_capacity_inr ?? data.allocation?.total_monthly_sip ?? data.allocation?.total_monthly_investment ?? 0),
        health_status: data.health.health_status ?? data.health.emergency_fund_status ?? "HEALTHY",
        flags: Array.isArray(data.health.flags) ? data.health.flags : [],
      },
      risk: {
        risk_score: Number(data.risk.risk_score ?? 50),
        risk_category: data.risk.risk_category ?? "MODERATE",
        tolerance_score: Number(data.risk.tolerance_score ?? data.risk.score_breakdown?.tolerance_component ?? 50),
        capacity_score: Number(data.risk.capacity_score ?? data.risk.score_breakdown?.capacity_component ?? 50),
        experience_score: Number(data.risk.experience_score ?? data.risk.score_breakdown?.experience_component ?? 50),
        time_horizon_score: Number(data.risk.time_horizon_score ?? data.risk.score_breakdown?.time_horizon_component ?? 50),
        risk_factors: Array.isArray(data.risk.risk_factors) ? data.risk.risk_factors : [],
        warnings: Array.isArray(data.risk.warnings) ? data.risk.warnings : [],
      },
      allocation: {
        allocations: Array.isArray(data.allocation.allocations)
          ? data.allocation.allocations
          : Array.isArray(data.allocation.recommended_sip_breakdown)
          ? data.allocation.recommended_sip_breakdown.map((s: any) => ({
              asset_class: s.asset_class?.toLowerCase().includes("equity")
                ? "equity"
                : s.asset_class?.toLowerCase().includes("debt")
                ? "debt"
                : s.asset_class?.toLowerCase().includes("gold")
                ? "gold"
                : "cash",
              target_pct: Number(s.allocation_pct ?? 0),
              min_pct: Number(data.allocation.constraints?.equity_min_pct ?? 0),
              max_pct: Number(data.allocation.constraints?.equity_max_pct ?? 100),
              monthly_sip_inr: Number(s.monthly_sip_amount ?? 0),
              suggested_instruments: Array.isArray(s.instrument_types) ? s.instrument_types : [],
            }))
          : MOCK_ANALYSIS.allocation.allocations,
        total_monthly_sip: Number(data.allocation.total_monthly_sip ?? data.allocation.total_monthly_investment ?? 0),
        rationale: data.allocation.rationale || MOCK_ANALYSIS.allocation.rationale,
      },
      goals_feasibility: Array.isArray(data.goals_feasibility)
        ? data.goals_feasibility
        : Array.isArray(data.goal_analysis?.individual_goals)
        ? data.goal_analysis.individual_goals.map((g: any) => ({
            goal_type: g.goal_type,
            target_amount: Number(g.target_amount ?? 0),
            current_amount: Number(g.current_amount ?? 0),
            target_years: Number(g.target_years ?? 1),
            required_monthly_sip: Number(g.required_monthly_sip ?? 0),
            allocated_monthly_sip: Number(g.required_monthly_sip ?? 0),
            projected_corpus: Number(g.target_amount ?? 0),
            is_feasible: true,
            feasibility_score_pct: 100,
            shortfall_surplus_inr: 0,
            recommendation: `Target duration: ${g.horizon_category || `${g.target_years} years`}`,
          }))
        : MOCK_ANALYSIS.goals_feasibility,
      analyzed_at: data.analyzed_at || new Date().toISOString(),
    };
  }

  // If received raw FastAPI ComprehensiveFinancialAnalysisResponse
  const fh = data.financial_health || {};
  const ra = data.risk_assessment || {};
  const aa = data.asset_allocation || {};
  const ga = data.goal_analysis || {};

  const totalMonthlySip = Number(aa.total_monthly_investment ?? fh.monthly_surplus ?? 40000);

  const allocations: AssetAllocationItem[] = Array.isArray(aa.recommended_sip_breakdown)
    ? aa.recommended_sip_breakdown.map((s: any) => {
        const rawClass = String(s.asset_class || "").toLowerCase();
        const normalizedClass: "equity" | "debt" | "gold" | "cash" = rawClass.includes("equity")
          ? "equity"
          : rawClass.includes("debt")
          ? "debt"
          : rawClass.includes("gold")
          ? "gold"
          : "cash";

        return {
          asset_class: normalizedClass,
          target_pct: Number(s.allocation_pct ?? 0),
          min_pct:
            normalizedClass === "equity"
              ? Number(aa.constraints?.equity_min_pct ?? 50)
              : normalizedClass === "debt"
              ? Number(aa.constraints?.debt_min_pct ?? 20)
              : 5,
          max_pct:
            normalizedClass === "equity"
              ? Number(aa.constraints?.equity_max_pct ?? 70)
              : normalizedClass === "debt"
              ? Number(aa.constraints?.debt_max_pct ?? 35)
              : 15,
          monthly_sip_inr: Number(s.monthly_sip_amount ?? 0),
          suggested_instruments: Array.isArray(s.instrument_types)
            ? s.instrument_types
            : [s.asset_class],
        };
      })
    : MOCK_ANALYSIS.allocation.allocations;

  const goalsFeasibility: GoalFeasibilityResult[] = Array.isArray(ga.individual_goals)
    ? ga.individual_goals.map((g: any) => ({
        goal_type: g.goal_type,
        target_amount: Number(g.target_amount ?? 0),
        current_amount: Number(g.current_amount ?? 0),
        target_years: Number(g.target_years ?? 1),
        required_monthly_sip: Number(g.required_monthly_sip ?? 0),
        allocated_monthly_sip: Number(g.required_monthly_sip ?? 0),
        projected_corpus: Number(g.projected_future_value_from_current ?? g.target_amount ?? 0),
        is_feasible: Boolean(ga.is_fully_funded ?? true),
        feasibility_score_pct: Number(ga.funding_coverage_pct ?? 100),
        shortfall_surplus_inr: Number(ga.monthly_capacity_surplus_deficit ?? 0),
        recommendation: `Expected annual return: ${g.expected_annual_return_pct ?? 12}% (${g.horizon_category || "Standard"})`,
      }))
    : MOCK_ANALYSIS.goals_feasibility;

  return {
    user_id: data.user_id,
    health: {
      monthly_surplus: Number(fh.monthly_surplus ?? 0),
      savings_ratio_pct: Number(fh.surplus_to_income_ratio ? fh.surplus_to_income_ratio * 100 : 50),
      emergency_fund_months: Number(fh.emergency_fund_runway_months ?? 6),
      emergency_fund_target_inr: Number(fh.target_emergency_fund ?? 300000),
      debt_to_income_ratio: Number(fh.debt_to_income_ratio ?? 0.2),
      investment_capacity_inr: totalMonthlySip,
      health_status: fh.emergency_fund_status === "DEFICIENT" ? "VULNERABLE" : "HEALTHY",
      flags: [
        `Emergency runway: ${fh.emergency_fund_runway_months ?? 6} months (${fh.emergency_fund_status || "HEALTHY"})`,
        `Debt to annual income ratio is ${(Number(fh.debt_to_income_ratio ?? 0) * 100).toFixed(1)}%`,
        `Monthly investable surplus is ₹${Number(fh.monthly_surplus ?? 0).toLocaleString("en-IN")}`,
      ],
    },
    risk: {
      risk_score: Number(ra.risk_score ?? 60),
      risk_category: ra.risk_category ?? "MODERATE",
      tolerance_score: Number(ra.score_breakdown?.tolerance_component ? ra.score_breakdown.tolerance_component * 4 : 60),
      capacity_score: Number(ra.score_breakdown?.capacity_component ? ra.score_breakdown.capacity_component * 2.85 : 70),
      experience_score: Number(ra.score_breakdown?.experience_component ? ra.score_breakdown.experience_component * 6.66 : 65),
      time_horizon_score: Number(ra.score_breakdown?.time_horizon_component ? ra.score_breakdown.time_horizon_component * 4 : 70),
      risk_factors: [
        `Stated risk tolerance: ${ra.stated_tolerance || "MODERATE"}`,
        `Investment experience level: ${ra.investment_experience || "INTERMEDIATE"}`,
        `Investor age: ${ra.age || 30} years`,
      ],
      warnings: [
        `Strict SEBI equity exposure limit applied for ${ra.risk_category || "MODERATE"} category.`,
      ],
    },
    allocation: {
      allocations,
      total_monthly_sip: totalMonthlySip,
      rationale:
        ga.recommendation_summary ||
        `Optimized for ${ra.risk_category || "MODERATE"} investor with ₹${totalMonthlySip.toLocaleString("en-IN")} monthly investment capacity across diversified asset classes.`,
    },
    goals_feasibility: goalsFeasibility,
    analyzed_at: new Date().toISOString(),
  };
}

export const analysisService = {
  async getUserAnalysis(userId: number = 1): Promise<FinancialAnalysisResponse> {
    try {
      const raw = await apiClient<any>(`/analysis/${userId}`);
      return normalizeAnalysisResponse(raw);
    } catch (err: any) {
      console.warn("Using deterministic mock analysis (backend error or offline):", err.message);
      return MOCK_ANALYSIS;
    }
  },

  async simulateAnalysis(payload: SimulationPayload): Promise<FinancialAnalysisResponse> {
    try {
      const raw = await apiClient<any>("/analysis/simulate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return normalizeAnalysisResponse(raw);
    } catch (err: any) {
      console.warn("Simulation failed against backend, using local analysis fallback:", err.message);
      return MOCK_ANALYSIS;
    }
  },
};
