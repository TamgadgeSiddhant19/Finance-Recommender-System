export type ProductType = "mutual_fund" | "etf" | "stock" | "bond" | "fixed_deposit" | "gold_fund";
export type AssetClass = "equity" | "debt" | "gold" | "cash" | "hybrid";
export type RiskLevel = "low" | "low_to_moderate" | "moderate" | "moderately_high" | "high" | "very_high";

export interface FinancialProduct {
  id: number;
  symbol: string;
  name: string;
  product_type: ProductType;
  asset_class: AssetClass;
  issuer: string;
  currency: string;
  country: string;
  risk_level: RiskLevel;
  expense_ratio?: number;
  minimum_investment?: number;
  created_at: string;
}

export interface MarketDataPoint {
  id: number;
  financial_product_id: number;
  timestamp: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  source: string;
}
