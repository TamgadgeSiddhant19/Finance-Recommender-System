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
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Generate Your Official SEBI Recommendation</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300 max-w-lg mx-auto leading-relaxed">
              Your profile and {goals.length} active goals are configured. The Deterministic Engine will synthesize asset allocation bounds, score verified products, and produce an audited investment roadmap.
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
              Generate Deterministic Recommendation
            </Button>
          </div>
        </Card>
      </main>
    );
  }

  // 4. Recommendation Generated — Display Live Report
  const portfolioItems = recommendation.portfolio_items || [];
  const targetAlloc = recommendation.target_allocation;
  const totalSip = recommendation.total_monthly_sip;
  const validation = recommendation.validation_report;

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Header with Timestamp & Re-generate */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <FileCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            Official Financial Recommendation Report
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Deterministic asset synthesis aligned with SEBI risk bounds, verified Indian instruments, and tax rules.
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

      {/* Executive Summary Card */}
      <Card className="bg-gradient-to-r from-emerald-50 via-white to-white dark:from-emerald-950/30 dark:via-slate-900 dark:to-slate-900 border-emerald-200 dark:border-emerald-500/30 shadow-xs">
        <CardContent className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
              Executive Synthesis
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
              Profile: {recommendation.risk_category} ({recommendation.risk_score}/100)
            </span>
          </div>

          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            Multi-asset capital allocation formulated for {recommendation.risk_category} profile with monthly capacity of {formatINR(recommendation.monthly_investment_capacity)}. Asset distribution is mathematically verified to satisfy SEBI equity bounds and liquid emergency runway constraints.
          </p>

          <div className="pt-2 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-slate-800/80 text-xs">
            <div>
              <span className="text-slate-400">Total Monthly SIP:</span>
              <p className="text-base font-bold text-emerald-400">{formatINR(totalSip)}</p>
            </div>
            <div>
              <span className="text-slate-400">Target Equity Exposure:</span>
              <p className="text-base font-bold text-slate-100">{targetAlloc?.equity_pct ?? 0}%</p>
            </div>
            <div>
              <span className="text-slate-400">Target Debt Exposure:</span>
              <p className="text-base font-bold text-sky-400">{targetAlloc?.debt_pct ?? 0}%</p>
            </div>
            <div>
              <span className="text-slate-400">Validation Status:</span>
              <p className="text-base font-bold text-emerald-400">
                {validation?.is_valid ? "SEBI Rule-Validated" : "Conditional"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actionable Allocation Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Recommended Monthly Capital Deployment
          </CardTitle>
          <CardDescription>Selected SEBI-approved financial products with exact monthly SIP amounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-800/80">
            {portfolioItems.map((item, idx) => (
              <div key={item.product_id || idx} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1 md:w-1/3">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100 text-sm">{item.name}</span>
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
                  <p className="text-xs text-slate-400">
                    Ticker: <strong className="text-slate-300">{item.symbol}</strong> • Suitability Score: <strong className="text-emerald-400">{Number(item.suitability_score ?? 0).toFixed(1)}/100</strong>
                  </p>
                </div>

                <div className="md:w-1/3">
                  <span className="text-xs text-slate-400">Recommended Monthly SIP</span>
                  <p className="text-lg font-extrabold text-emerald-400">{formatINR(item.suggested_monthly_sip)}/mo</p>
                </div>

                <div className="md:w-1/3 text-xs space-y-1">
                  <span className="text-slate-400 font-semibold">Selection Rationale:</span>
                  {(item.selection_reasons || []).map((r, rIdx) => (
                    <p key={rIdx} className="text-slate-300 text-[11px]">• {typeof r === "string" ? r : r.description}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Goal Alignment & Regulatory Sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sky-400">
              <TrendingUp className="w-4 h-4" />
              Goal Compounding Feasibility
            </CardTitle>
            <CardDescription>Mathematical feasibility based on required vs allocated SIP</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            {analysis?.goals_feasibility?.map((gf, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-200">{gf.goal_type.replace(/_/g, " ")}</span>
                  <Badge variant={gf.is_feasible ? "emerald" : "amber"} size="sm">
                    {gf.is_feasible ? "Achievable" : "Requires Adjustment"}
                  </Badge>
                </div>
                <div className="flex justify-between text-slate-400 text-[11px]">
                  <span>Target: {formatINR(gf.target_amount)} ({gf.target_years} yrs)</span>
                  <span>Required SIP: <strong className="text-slate-200">{formatINR(gf.required_monthly_sip)}</strong></span>
                </div>
                <p className="text-[11px] text-slate-300 pt-1">
                  {gf.recommendation}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Regulatory & Institutional Sources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              Supporting Statutory Authorities
            </CardTitle>
            <CardDescription>Official regulations supporting this portfolio formulation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span>SEBI Mutual Funds Regulations, 1996</span>
                <Badge variant="blue" size="sm">Equity Mandates</Badge>
              </div>
              <p className="text-[11px] text-slate-400">
                Large Cap mandate requiring minimum 80% investment in top 100 market capitalization equities.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span>Income Tax Act (CBDT Finance Act 2024)</span>
                <Badge variant="emerald" size="sm">Tax Efficiency</Badge>
              </div>
              <p className="text-[11px] text-slate-400">
                Section 112A ₹1.25 Lakh LTCG annual exemption and Section 50AA debt fund taxation guidelines.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-1">
              <div className="flex items-center justify-between font-semibold text-slate-200">
                <span>Reserve Bank of India &amp; DICGC Guidelines</span>
                <Badge variant="amber" size="sm">Capital Safety</Badge>
              </div>
              <p className="text-[11px] text-slate-400">
                DICGC ₹5,00,000 principal + interest deposit guarantee per bank and SGB sovereign backing.
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between items-center pt-2">
            <span className="text-[11px] text-slate-400">Have questions about tax or regulations?</span>
            <Link href="/advisor">
              <Button size="sm" variant="outline" className="text-xs">
                Ask AI Advisor
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    </main>
  );
}
