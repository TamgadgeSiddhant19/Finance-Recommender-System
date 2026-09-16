"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { formatINR } from "@/lib/utils";
import {
  Sparkles,
  ShieldCheck,
  Layers,
  TrendingUp,
  FileCheck,
  Clock,
  UserPlus,
  Target,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Compass,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react";

export default function RecommendationsPage() {
  return (
    <ProtectedRoute>
      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <Sidebar />

        <RecommendationsContent />
      </div>
    </ProtectedRoute>
  );
}

function RecommendationsContent() {
  const {
    analysis,
    profile,
    goals,
    recommendation,
    hasProfile,
    hasGoals,
    hasRecommendation,
    generateRecommendation,
    isLoading,
  } = useFinancialData();

  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await generateRecommendation();
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-8 w-80" />
        <Skeleton className="h-44 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </main>
    );
  }

  // 1. Missing Profile
  if (!hasProfile || !profile) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-2xl mx-auto space-y-6 flex flex-col justify-center">
        <Card className="p-8 text-center space-y-4 border-emerald-500/30 bg-slate-900/60 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Financial Profile Required</h3>
            <p className="text-xs text-slate-300 max-w-md mx-auto mt-1 leading-relaxed">
              Complete your financial profile before generating a recommendation. The engine requires your monthly surplus, liabilities, and risk tolerance.
            </p>
          </div>
          <Link href="/profile">
            <Button className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white">
              Complete Financial Profile
            </Button>
          </Link>
        </Card>
      </main>
    );
  }

  // 2. Missing Goals
  if (!hasGoals || goals.length === 0) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-2xl mx-auto space-y-6 flex flex-col justify-center">
        <Card className="p-8 text-center space-y-4 border-sky-500/30 bg-slate-900/60 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mx-auto">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Financial Goal Required</h3>
            <p className="text-xs text-slate-300 max-w-md mx-auto mt-1 leading-relaxed">
              Add at least one financial goal (e.g. Retirement, House Downpayment, Emergency Fund) to calculate compounding horizons and instrument suitability.
            </p>
          </div>
          <Link href="/goals">
            <Button className="gap-2 bg-sky-600 hover:bg-sky-500 text-white">
              Create Your First Goal
            </Button>
          </Link>
        </Card>
      </main>
    );
  }

  // 3. Profile & Goals Exist, but Recommendation Not Generated Yet
  if (!hasRecommendation || !recommendation) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-3xl mx-auto space-y-6 flex flex-col justify-center">
        <Card className="p-8 text-center space-y-6 border-emerald-500/30 bg-white dark:bg-slate-900/70 shadow-xs dark:shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mx-auto">
            <Sparkles className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Generate Goal-Aware Portfolio Recommendation</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300 max-w-lg mx-auto leading-relaxed">
              Your profile and {goals.length} active goal{goals.length > 1 ? "s are" : " is"} configured. The Deterministic Engine will synthesize goal horizons, inflation indexation, feasibility status, and SEBI-aligned product allocations.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 max-w-md mx-auto grid grid-cols-2 gap-4 text-left text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400">Monthly Capacity:</span>
              <p className="font-bold text-emerald-700 dark:text-emerald-400 text-sm">{formatINR(profile.monthly_investment_capacity || (profile.monthly_income - profile.monthly_expenses))}</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Risk Profile:</span>
              <p className="font-bold text-slate-900 dark:text-slate-200 text-sm">{analysis?.risk?.risk_category || profile.risk_tolerance}</p>
            </div>
          </div>

          <div>
            <Button
              size="lg"
              onClick={handleGenerate}
              isLoading={isGenerating}
              className="px-8 gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md"
            >
              <Sparkles className="w-4 h-4" />
              Generate Goal-Aware Recommendation
            </Button>
          </div>
        </Card>
      </main>
    );
  }

  // 4. Recommendation Generated — Display Live Goal-Aware Report
  const portfolioItems = recommendation.portfolio_items || [];
  const targetAlloc = recommendation.target_allocation;
  const totalSip = recommendation.total_monthly_sip;
  const validation = recommendation.validation_report;
  const allocReasons = recommendation.allocation_reasons || {};
  const fundingActions = recommendation.funding_gap_actions || [];
  const goalsBreakdown = recommendation.goals_breakdown || [];
  const excludedProducts = recommendation.excluded_products || [];
  const horizonBucket = recommendation.goal_horizon_bucket || "GENERAL_WEALTH";
  const feasibilityStatus = recommendation.goal_feasibility_status || "ON_TRACK";
  const [showExcluded, setShowExcluded] = useState(false);

  const getFeasibilityBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case "ON_TRACK":
        return <Badge variant="emerald" size="md"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> ON TRACK</Badge>;
      case "MODERATELY_UNDERFUNDED":
        return <Badge variant="amber" size="md"><AlertCircle className="w-3.5 h-3.5 mr-1" /> MODERATELY UNDERFUNDED</Badge>;
      case "SIGNIFICANTLY_UNDERFUNDED":
        return <Badge variant="amber" size="md"><AlertCircle className="w-3.5 h-3.5 mr-1" /> SIGNIFICANTLY UNDERFUNDED</Badge>;
      case "NOT_FEASIBLE":
        return <Badge variant="rose" size="md"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> INTERVENTION REQUIRED</Badge>;
      default:
        return <Badge variant="slate" size="md">{status}</Badge>;
    }
  };

  const getHorizonBadge = (bucket: string) => {
    switch (bucket?.toUpperCase()) {
      case "SHORT_TERM":
        return <Badge variant="blue" size="sm">SHORT-TERM (&lt; 3 YRS)</Badge>;
      case "MEDIUM_TERM":
        return <Badge variant="emerald" size="sm">MEDIUM-TERM (3–5 YRS)</Badge>;
      case "LONG_TERM":
        return <Badge variant="emerald" size="sm">LONG-TERM (&gt; 5 YRS)</Badge>;
      default:
        return <Badge variant="slate" size="sm">GENERAL WEALTH</Badge>;
    }
  };

  const getDataSourceBadge = (source?: string, status?: string) => {
    const src = (source || "master_catalog").toLowerCase();
    const stat = (status || "").toLowerCase();

    if (src.includes("alpha") || src.includes("alphavantage")) {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
          Alpha Vantage ({stat === "live" ? "Live" : "Historical"})
        </span>
      );
    }
    if (src.includes("demo") || stat === "synthetic") {
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
          Demo (Synthetic)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
        Catalog Baseline
      </span>
    );
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header with Timestamp & Re-generate */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <FileCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            Product Intelligence &amp; Asset Allocation
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Deterministic suitability ranking combining SEBI risk guardrails, goal horizons, and market intelligence metrics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="emerald" size="md">
            <Clock className="w-3 h-3 mr-1" />
            Saved: {recommendation.created_at ? new Date(recommendation.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "Active Session"}
          </Badge>

          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerate}
            isLoading={isGenerating}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className="w-3 h-3" />
            Re-Calculate
          </Button>
        </div>
      </div>

      {/* 1. Goal Context & Feasibility Overview */}
      <Card className="bg-gradient-to-r from-emerald-50 via-white to-white dark:from-emerald-950/30 dark:via-slate-900 dark:to-slate-900 border-emerald-200 dark:border-emerald-500/30 shadow-xs">
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                Primary Goal Feasibility
              </span>
              {getHorizonBadge(horizonBucket)}
            </div>
            <div>
              {getFeasibilityBadge(feasibilityStatus)}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-2">
            <div>
              <span className="text-slate-500 dark:text-slate-400">Nominal Target:</span>
              <p className="text-base font-bold text-slate-900 dark:text-slate-100">
                {recommendation.nominal_target ? formatINR(recommendation.nominal_target) : formatINR(goals[0]?.target_amount || 0)}
              </p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Inflation-Adjusted Target:</span>
              <p className="text-base font-bold text-amber-600 dark:text-amber-400">
                {recommendation.inflation_adjusted_target ? formatINR(recommendation.inflation_adjusted_target) : "—"}
              </p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Projected Corpus:</span>
              <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                {recommendation.projected_corpus ? formatINR(recommendation.projected_corpus) : "—"}
              </p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Funding Ratio:</span>
              <p className="text-base font-bold text-sky-600 dark:text-sky-400">
                {recommendation.funding_ratio !== undefined && recommendation.funding_ratio !== null ? `${Number(recommendation.funding_ratio).toFixed(1)}%` : "100.0%"}
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-500 dark:text-slate-400">Evaluated Risk Profile:</span>
              <p className="font-semibold text-slate-800 dark:text-slate-200">{recommendation.risk_category} ({recommendation.risk_score}/100)</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Monthly Investment Allocated:</span>
              <p className="font-semibold text-emerald-600 dark:text-emerald-400">{formatINR(totalSip)}/mo</p>
            </div>
            <div>
              <span className="text-slate-500 dark:text-slate-400">Horizon Strategy:</span>
              <p className="font-semibold text-slate-800 dark:text-slate-200">
                {horizonBucket === "SHORT_TERM" ? "Capital Preservation & Sequence Defense" : horizonBucket === "MEDIUM_TERM" ? "Balanced Volatility Dampening" : "Long-Term Equity Compounding"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Goal-Aware Target Allocation & Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-emerald-500/30 bg-emerald-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase">Equity</span>
            <Badge variant="emerald" size="sm">{targetAlloc?.equity_pct ?? 0}%</Badge>
          </div>
          <div className="mt-2 text-xs text-slate-600 dark:text-slate-300 space-y-1">
            <p className="font-semibold text-slate-800 dark:text-slate-100">
              {formatINR(((recommendation.monthly_investment_capacity || totalSip) * (targetAlloc?.equity_pct ?? 0)) / 100)}/mo
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              {allocReasons.equity || "Growth exposure respecting risk ceilings."}
            </p>
          </div>
        </Card>

        <Card className="p-4 border-sky-500/30 bg-sky-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-sky-700 dark:text-sky-400 uppercase">Debt / Fixed Income</span>
            <Badge variant="blue" size="sm">{targetAlloc?.debt_pct ?? 0}%</Badge>
          </div>
          <div className="mt-2 text-xs text-slate-600 dark:text-slate-300 space-y-1">
            <p className="font-semibold text-slate-800 dark:text-slate-100">
              {formatINR(((recommendation.monthly_investment_capacity || totalSip) * (targetAlloc?.debt_pct ?? 0)) / 100)}/mo
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              {allocReasons.debt || "Capital stability and predictable yield."}
            </p>
          </div>
        </Card>

        <Card className="p-4 border-amber-500/30 bg-amber-500/5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase">Gold</span>
            <Badge variant="amber" size="sm">{targetAlloc?.gold_pct ?? 0}%</Badge>
          </div>
          <div className="mt-2 text-xs text-slate-600 dark:text-slate-300 space-y-1">
            <p className="font-semibold text-slate-800 dark:text-slate-100">
              {formatINR(((recommendation.monthly_investment_capacity || totalSip) * (targetAlloc?.gold_pct ?? 0)) / 100)}/mo
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              {allocReasons.gold || "Inflation hedge and non-correlated diversification."}
            </p>
          </div>
        </Card>

        <Card className="p-4 border-slate-700 bg-slate-800/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase">Cash / Liquid</span>
            <Badge variant="slate" size="sm">{targetAlloc?.cash_pct ?? 0}%</Badge>
          </div>
          <div className="mt-2 text-xs text-slate-300 space-y-1">
            <p className="font-semibold text-slate-100">
              {formatINR(((recommendation.monthly_investment_capacity || totalSip) * (targetAlloc?.cash_pct ?? 0)) / 100)}/mo
            </p>
            <p className="text-[11px] text-slate-400 leading-snug">
              {allocReasons.cash || "Immediate liquidity and near-term capital security."}
            </p>
          </div>
        </Card>
      </div>

      {/* 3. Why This Allocation & Funding Gap Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Why This Allocation */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <Compass className="w-4 h-4" />
              Why This Allocation (Deterministic Rationale)
            </CardTitle>
            <CardDescription>Rule-based mathematical justifications based on goal horizon and risk limits</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 space-y-1">
              <span className="font-bold text-emerald-700 dark:text-emerald-400">Equity ({targetAlloc?.equity_pct}%)</span>
              <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                {allocReasons.equity || "Allocated based on horizon runway and risk profile ceiling."}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 space-y-1">
              <span className="font-bold text-sky-700 dark:text-sky-400">Debt &amp; Fixed Income ({targetAlloc?.debt_pct}%)</span>
              <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                {allocReasons.debt || "Guards capital stability as timeline progresses."}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 space-y-1">
              <span className="font-bold text-amber-700 dark:text-amber-400">Commodity / Gold ({targetAlloc?.gold_pct}%)</span>
              <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">
                {allocReasons.gold || "Diversification pillar mitigating rupee purchasing power erosion."}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Actionable Funding Gap Advice */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sky-600 dark:text-sky-400">
              <TrendingUp className="w-4 h-4" />
              Funding Optimization &amp; Action Plan
            </CardTitle>
            <CardDescription>Actionable steps to reach 100% funding without increasing risk</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            {fundingActions.length > 0 ? (
              fundingActions.map((action, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-sky-50 dark:bg-slate-800/40 border border-sky-200 dark:border-slate-700/50 flex items-start gap-2.5">
                  <ArrowUpRight className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0 mt-0.5" />
                  <p className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">{action}</p>
                </div>
              ))
            ) : (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300">
                Your investment trajectory is fully funded. Continue regular monthly investments and review asset allocation annually.
              </div>
            )}

            <div className="p-2.5 rounded-lg bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/40 text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>
                <strong>Guardrail Guarantee:</strong> Funding gaps will never cause the engine to recommend higher-risk speculative assets.
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4. Actionable Product Selection Matrix with Intelligence Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Recommended Products &amp; Product Intelligence Analysis
          </CardTitle>
          <CardDescription>
            Selected SEBI-approved instruments with multi-factor suitability scoring, risk-adjusted metrics, and data provenance.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-200 dark:divide-slate-800/80">
            {portfolioItems.map((item, idx) => (
              <div key={item.product_id || idx} className="py-4 space-y-3">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  {/* Left Column: Product info & Suitability */}
                  <div className="space-y-1.5 md:w-1/3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">{item.name}</span>
                      <Badge
                        variant={
                          item.asset_class?.toLowerCase().includes("equity")
                            ? "emerald"
                            : item.asset_class?.toLowerCase().includes("debt")
                            ? "blue"
                            : item.asset_class?.toLowerCase().includes("gold")
                            ? "amber"
                            : "slate"
                        }
                        size="sm"
                      >
                        {item.allocation_percentage}% Weight
                      </Badge>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <span>Ticker: <strong className="text-slate-700 dark:text-slate-300">{item.symbol}</strong></span>
                      <span>•</span>
                      <span>Risk: <strong className="capitalize text-slate-700 dark:text-slate-300">{item.risk_level?.replace("_", " ")}</strong></span>
                      <span>•</span>
                      {getDataSourceBadge(item.data_source, item.data_status)}
                    </div>

                    <div className="flex items-center gap-2 pt-0.5">
                      <span className="text-xs text-slate-500 dark:text-slate-400">Suitability Score:</span>
                      <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400">
                        {Number(item.suitability_score ?? 0).toFixed(1)}/100
                      </span>
                    </div>
                  </div>

                  {/* Middle Column: SIP & Intelligence Metrics */}
                  <div className="md:w-1/3 space-y-2">
                    <div>
                      <span className="text-xs text-slate-500 dark:text-slate-400">Recommended Monthly SIP</span>
                      <p className="text-lg font-extrabold text-emerald-600 dark:text-emerald-400">{formatINR(item.suggested_monthly_sip)}/mo</p>
                    </div>

                    {/* Historical Market Intelligence Grid */}
                    <div className="grid grid-cols-3 gap-2 p-2 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/40 text-[10px]">
                      <div>
                        <span className="text-slate-400 block">1Y Return</span>
                        <span className={`font-semibold ${(item.historical_return_1y ?? 0) >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                          {item.historical_return_1y !== undefined && item.historical_return_1y !== null ? `${item.historical_return_1y > 0 ? "+" : ""}${Number(item.historical_return_1y).toFixed(1)}%` : "N/A"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Volatility (Ann.)</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {item.volatility !== undefined && item.volatility !== null ? `${Number(item.volatility).toFixed(1)}%` : "N/A"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block">Max Drawdown</span>
                        <span className="font-semibold text-amber-600 dark:text-amber-400">
                          {item.max_drawdown !== undefined && item.max_drawdown !== null ? `${Number(item.max_drawdown).toFixed(1)}%` : "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Selection Rationale Breakdown */}
                  <div className="md:w-1/3 text-xs space-y-1.5">
                    <span className="text-slate-500 dark:text-slate-400 font-semibold block">Why Selected (Factor Breakdown):</span>
                    <div className="space-y-1">
                      {(item.selection_reasons || []).map((r, rIdx) => (
                        <div key={rIdx} className="text-slate-600 dark:text-slate-300 text-[11px] flex items-start gap-1.5">
                          <span className="text-emerald-500 font-bold shrink-0">•</span>
                          <span>{typeof r === "string" ? r : r.description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 5. Excluded Products Audit Trail */}
      {excludedProducts.length > 0 && (
        <Card className="border-slate-200 dark:border-slate-800">
          <CardHeader className="cursor-pointer" onClick={() => setShowExcluded(!showExcluded)}>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                  <ShieldAlert className="w-4 h-4 text-slate-400" />
                  Why Other Products Were Excluded ({excludedProducts.length} items screened out)
                </CardTitle>
                <CardDescription className="text-xs">
                  Transparent suitability audit trail showing why non-recommended catalog products were rejected.
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" className="text-xs text-slate-500">
                {showExcluded ? "Hide Excluded Items" : "View Excluded Items"}
              </Button>
            </div>
          </CardHeader>

          {showExcluded && (
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="text-[11px] uppercase text-slate-400 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="py-2 pr-4">Product</th>
                      <th className="py-2 pr-4">Asset Class</th>
                      <th className="py-2 pr-4">Risk Level</th>
                      <th className="py-2 pr-4">Exclusion Stage</th>
                      <th className="py-2">Deterministic Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                    {excludedProducts.map((ex, exIdx) => (
                      <tr key={ex.product_id || exIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="py-2.5 pr-4 font-semibold text-slate-800 dark:text-slate-200">
                          {ex.name} <span className="text-slate-400 text-[10px]">({ex.symbol})</span>
                        </td>
                        <td className="py-2.5 pr-4 capitalize text-slate-600 dark:text-slate-400">{ex.asset_class || "—"}</td>
                        <td className="py-2.5 pr-4 capitalize text-slate-600 dark:text-slate-400">{ex.risk_level?.replace("_", " ") || "—"}</td>
                        <td className="py-2.5 pr-4">
                          <Badge variant="slate" size="sm" className="text-[10px] capitalize">
                            {ex.category?.replace("_", " ") || "Filter"}
                          </Badge>
                        </td>
                        <td className="py-2.5 text-slate-600 dark:text-slate-300 text-[11px] leading-tight">
                          {ex.reason}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* 6. Multi-Goal Priority Breakdown (If multiple goals exist) */}
      {goalsBreakdown.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sky-400">
              <Target className="w-4 h-4" />
              Multi-Goal Priority Distribution
            </CardTitle>
            <CardDescription>Individual goal feasibility and priority-based SIP allocation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {goalsBreakdown.map((g, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-slate-100 capitalize">{g.goal_type.replace(/_/g, " ")}</span>
                    <Badge variant={g.priority === "high" ? "emerald" : g.priority === "medium" ? "blue" : "slate"} size="sm">
                      {g.priority.toUpperCase()} PRIORITY
                    </Badge>
                  </div>
                  <div className="flex justify-between text-slate-500 dark:text-slate-400 text-[11px]">
                    <span>Target: {formatINR(g.target_amount)} ({g.target_years} yrs)</span>
                    <span>Funding: <strong className="text-slate-800 dark:text-slate-200">{Number(g.funding_ratio_pct).toFixed(1)}%</strong></span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-slate-200 dark:border-slate-700/40 text-[11px]">
                    <span className="text-slate-500 dark:text-slate-400">Allocated SIP:</span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatINR(g.allocated_monthly_sip)}/mo</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 7. Regulatory Disclaimers & Performance Integrity Notice */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-1.5 leading-relaxed">
        <p className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
          Financial &amp; Market Intelligence Disclaimer
        </p>
        <p>
          Historical returns, annualized volatility, and drawdown statistics are provided for informational and analytical purposes only. Past performance is not indicative of future returns. Product intelligence scoring strictly bounds market performance weight (5%) and penalizes high volatility/drawdowns to prevent return chasing. All recommendations are computed deterministically under SEBI risk suitability rules.
        </p>
      </div>
    </main>
  );
}
