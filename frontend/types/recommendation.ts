import { FinancialProduct } from "./product";
import { FinancialGoal, UserProfile } from "./financial";

export interface ProductSelectionReason {
  category: string;
  description: string;
  score_contribution: number;
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
}
