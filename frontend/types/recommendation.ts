import { FinancialProduct } from "./product";
import { FinancialGoal, UserProfile } from "./financial";

export interface ProductSelectionReason {
  category: string;
  description: string;
  score_contribution: number;
}

export interface ProductExclusionSummary {
  product_id?: number;
  symbol: string;
  name: string;
  asset_class?: string;
  risk_level?: string;
  reason: string;
  category: string;
}

// -----------------------------------------------------------------------------
// Phase 7.4 Structured Explanation & Audit Types
// -----------------------------------------------------------------------------

export interface RiskExplanationFactor {
  factor_name: string;
  score_contribution: number;
  description: string;
}

export interface RiskExplanation {
  risk_score: number;
  risk_category: string;
  factors: RiskExplanationFactor[];
  summary: string;
}

export interface GoalExplanation {
  goal_type: string;
  nominal_target: number;
  inflation_adjusted_target: number;
  projected_corpus: number;
  funding_ratio_pct: number;
  feasibility_status: string;
  explanation: string;
}

export interface AssetAllocationExplanationItem {
  asset_class: string;
  allocation_percentage: number;
  sip_amount: number;
  reason: string;
  policy_rule: string;
}

export interface SelectedProductExplanation {
  symbol: string;
  name: string;
  asset_class: string;
  suitability_score: number;
  allocation_percentage: number;
  suggested_monthly_sip: number;
  metrics: Record<string, any>;
  selection_reasons: string[];
}

export interface ProductExclusionItem {
  symbol: string;
  name: string;
  asset_class?: string;
  risk_level?: string;
  suitability_score?: number;
  exclusion_type: "HARD_REJECTION" | "RANKED_LOWER" | string;
  reason: string;
}

export interface MarketDataProvenanceItem {
  symbol: string;
  data_source: string;
  data_status: string;
  data_as_of?: string;
  data_quality_score: number;
}

export interface RecommendationExplanation {
  summary: string;
  engine_version: string;
  policy_version: string;
  risk_explanation: RiskExplanation;
  goal_explanation?: GoalExplanation;
  allocation_explanation: AssetAllocationExplanationItem[];
  selected_products: SelectedProductExplanation[];
  excluded_products: ProductExclusionItem[];
  funding_gap_actions: string[];
  data_provenance: Record<string, MarketDataProvenanceItem>;
}

export interface DecisionTrace {
  user_id?: number;
  engine_version: string;
  policy_version: string;
  input_snapshot_hash: string;
  profile_snapshot: Record<string, any>;
  risk_assessment: Record<string, any>;
  financial_health: Record<string, any>;
  goals: Record<string, any>[];
  horizon_bucket: string;
  feasibility_status: string;
  target_allocation: Record<string, number>;
  guardrails_applied: string[];
  total_products_considered: number;
  hard_rejected_products: Record<string, any>[];
  eligible_products_count: number;
  ranked_lower_products: Record<string, any>[];
  selected_products: Record<string, any>[];
  market_data_provenance: Record<string, any>;
  validation_report: Record<string, any>;
}

export interface RecommendationAuditResponse {
  id: number;
  recommendation_id: number;
  user_id: number;
  engine_version: string;
  policy_version: string;
  schema_version: string;
  input_snapshot_hash: string;
  decision_trace: DecisionTrace;
  data_provenance: Record<string, any>;
  validation_result: Record<string, any>;
  created_at: string;
}

export interface RecommendedPortfolioItem {
  product_id: number;
  symbol: string;
  name: string;
  product_type: string;
  asset_class: "equity" | "debt" | "gold" | "cash" | "hybrid" | "other";
  risk_level: "low" | "moderate" | "high" | "very_high";
  suitability_score: number;
  allocation_percentage: number;
  suggested_monthly_sip: number;
  suggested_lump_sum: number;
  selection_reasons: ProductSelectionReason[];

  // Phase 7.3 Product Intelligence & Risk-Adjusted Analytics
  risk_compatibility_score?: number;
  goal_compatibility_score?: number;
  horizon_compatibility_score?: number;
  historical_return_1y?: number;
  historical_return_3y?: number;
  historical_return_5y?: number;
  volatility?: number;
  max_drawdown?: number;
  current_drawdown?: number;
  expense_ratio?: number;
  data_quality_score?: number;
  data_source?: string;
  data_status?: string;
  data_as_of?: string;
}

export interface ValidationCheck {
  check_name: string;
  passed: boolean;
  details: string;
}

export interface PortfolioValidationReport {
  is_valid: boolean;
  checks: ValidationCheck[];
  error_messages: string[];
  warning_messages: string[];
}

export interface TargetAllocationSummary {
  equity_pct: number;
  debt_pct: number;
  gold_pct: number;
  cash_pct: number;
}

export interface GoalRecommendationSummary {
  goal_id?: number;
  goal_type: string;
  target_amount: number;
  current_amount: number;
  target_years: number;
  priority: string;
  feasibility_status: string;
  funding_ratio_pct: number;
  projected_corpus: number;
  inflation_adjusted_target: number;
  shortfall_or_surplus: number;
  allocated_monthly_sip: number;
  required_monthly_sip: number;
  horizon_bucket: string;
  funding_gap_actions: string[];
}

export interface RecommendationResponse {
  recommendation_id?: number;
  user_id?: number;
  risk_category: string;
  risk_score: number;
  monthly_investment_capacity: number;
  target_allocation: TargetAllocationSummary;
  portfolio_items: RecommendedPortfolioItem[];
  total_monthly_sip: number;
  total_lump_sum: number;
  validation_report: PortfolioValidationReport;
  created_at: string;

  // Phase 7.2 Goal-Aware Allocation Extensions
  goal_horizon_bucket?: string;
  goal_feasibility_status?: string;
  nominal_target?: number;
  inflation_adjusted_target?: number;
  projected_corpus?: number;
  funding_ratio?: number;
  goal_shortfall_or_surplus?: number;
  goal_aware_allocation?: TargetAllocationSummary;
  allocation_reasons?: Record<string, string>;
  funding_gap_actions?: string[];
  goals_breakdown?: GoalRecommendationSummary[];

  // Phase 7.3 Product Intelligence Extensions
  excluded_products?: ProductExclusionSummary[];

  // Phase 7.4 Explainability & Audit Extensions
  engine_version?: string;
  policy_version?: string;
  input_snapshot_hash?: string;
  explanation?: RecommendationExplanation;
  decision_trace?: DecisionTrace;
}

export interface RecommendationSimulateRequest {
  profile: Partial<UserProfile>;
  goals: Partial<FinancialGoal>[];
  available_products?: FinancialProduct[];
}

export interface RecommendationHistoryItem {
  id: number;
  user_id: number;
  risk_category: string;
  risk_score: number;
  monthly_capacity: number;
  target_equity_pct: number;
  target_debt_pct: number;
  target_gold_pct: number;
  target_cash_pct: number;
  is_valid: boolean;
  created_at: string;
  goal_horizon_bucket?: string;
  goal_feasibility_status?: string;
}

