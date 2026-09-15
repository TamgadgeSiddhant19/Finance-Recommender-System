export type RiskTolerance = "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE";
export type InvestmentExperience = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
export type GoalType = "EMERGENCY_FUND" | "RETIREMENT" | "HOUSE" | "HOUSE_DOWNPAYMENT" | "EDUCATION" | "WEALTH_CREATION" | "OTHER";
export type GoalPriority = "HIGH" | "MEDIUM" | "LOW";

export interface UserProfile {
  id?: number;
  user_id?: number;
  age: number;
  monthly_income: number;
  monthly_expenses: number;
  total_savings: number;
  monthly_investment_capacity: number;
  total_debt: number;
  risk_tolerance: RiskTolerance;
  investment_experience: InvestmentExperience;
  created_at?: string;
  updated_at?: string;
}

export interface FinancialGoal {
  id?: number;
  user_id?: number;
  goal_type: GoalType;
  target_amount: number;
  current_amount: number;
  target_years: number;
  priority: GoalPriority;
  created_at?: string;
  updated_at?: string;
}

export interface FinancialHealthMetrics {
  monthly_surplus: number;
  savings_ratio_pct: number;
  emergency_fund_months: number;
  emergency_fund_target_inr: number;
  debt_to_income_ratio: number;
  investment_capacity_inr: number;
  health_status: "HEALTHY" | "MODERATE" | "VULNERABLE";
  flags: string[];
}

export interface RiskProfileMetrics {
  risk_score: number;
  risk_category: "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE" | "VERY_AGGRESSIVE";
  tolerance_score: number;
  capacity_score: number;
  experience_score: number;
  time_horizon_score: number;
  risk_factors: string[];
  warnings: string[];
}

export interface AssetAllocationItem {
  asset_class: "equity" | "debt" | "gold" | "cash";
  target_pct: number;
  min_pct: number;
  max_pct: number;
  monthly_sip_inr: number;
  suggested_instruments: string[];
}

export interface AssetAllocationMatrix {
  allocations: AssetAllocationItem[];
  total_monthly_sip: number;
  rationale: string;
}

export interface GoalFeasibilityResult {
  goal_type: GoalType;
  target_amount: number;
  current_amount: number;
  target_years: number;
  required_monthly_sip: number;
  allocated_monthly_sip: number;
  projected_corpus: number;
  is_feasible: boolean;
  feasibility_score_pct: number;
  shortfall_surplus_inr: number;
  recommendation: string;
}

export interface FinancialAnalysisResponse {
  user_id?: number;
  health: FinancialHealthMetrics;
  risk: RiskProfileMetrics;
  allocation: AssetAllocationMatrix;
  goals_feasibility: GoalFeasibilityResult[];
  analyzed_at: string;
}

export type GoalFeasibilityStatus =
  | "ON_TRACK"
  | "MODERATELY_UNDERFUNDED"
  | "SIGNIFICANTLY_UNDERFUNDED"
  | "NOT_FEASIBLE";

export interface CalculationAssumptions {
  compounding_frequency: string;
  sip_timing: string;
  inflation_model: string;
  disclaimer: string;
}

export interface GoalProjectionResponse {
  goal_id?: number;
  goal_type: GoalType;
  target_amount: number;
  current_amount: number;
  monthly_contribution: number;
  horizon_years: number;
  expected_annual_return_pct: number;
  inflation_rate_pct: number;
  inflation_adjusted_target: number;
  projected_current_growth: number;
  projected_sip_growth: number;
  projected_corpus: number;
  projected_shortfall_or_surplus: number;
  funding_ratio_pct: number;
  required_monthly_contribution: number;
  required_annual_return_pct?: number | null;
  feasibility_status: GoalFeasibilityStatus;
  assumptions: CalculationAssumptions;
  recommendations: string[];
}
