"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Wallet,
  ArrowUpRight,
  Target,
  Sparkles,
  AlertTriangle,
  ChevronRight,
  UserPlus,
  PlusCircle,
  TrendingUp,
  CheckCircle2,
  FileCheck,
  ArrowRight,
} from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { AllocationPieChart } from "@/components/charts/AllocationPieChart";
import { MonthlyCashflowChart } from "@/components/charts/MonthlyCashflowChart";
import { Skeleton } from "@/components/ui/Skeleton";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { MarketOverviewBar } from "@/components/market/MarketOverviewBar";
import { useFinancialData } from "@/hooks/useFinancialData";
import { formatINR, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="flex flex-col min-h-[calc(100vh-4rem)]">
        {/* Real-time Indian Market Quotes via Upstox */}
        <MarketOverviewBar />

        <div className="flex-1 flex">
          <Sidebar />

          <DashboardContent />
        </div>
      </div>
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const {
    profile,
    goals,
    analysis,
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
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 w-full rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Skeleton className="lg:col-span-5 h-72 rounded-xl" />
          <Skeleton className="lg:col-span-7 h-72 rounded-xl" />
        </div>
      </main>
    );
  }

  // =========================================================================
  // STATE A: New Authenticated User (No Profile Created Yet)
  // =========================================================================
  if (!hasProfile || !profile) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-8 flex flex-col justify-center">
        <Card className="p-6 sm:p-10 text-center space-y-6 border-emerald-500/30 bg-white dark:bg-slate-900/80 shadow-xs dark:shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mx-auto">
            <UserPlus className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Welcome! Let&apos;s build your financial profile.</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300 max-w-lg mx-auto leading-relaxed">
              ArthaAI uses deterministic mathematical algorithms and official SEBI &amp; RBI regulations to analyze your wealth. Provide your income, expenses, and savings to start.
            </p>
          </div>

          {/* 4-Step Progressive Roadmap */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-left max-w-3xl mx-auto text-xs">
            <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/40">
              <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block mb-1">Step 1 (Current)</span>
              <p className="font-semibold text-slate-900 dark:text-white">Financial Profile</p>
              <p className="text-slate-600 dark:text-slate-400 text-[11px] mt-0.5">Income, expenses, savings &amp; debt in INR.</p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50">
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1">Step 2</span>
              <p className="font-semibold text-slate-700 dark:text-slate-300">Financial Goals</p>
              <p className="text-slate-500 text-[11px] mt-0.5">Retirement, house, emergency fund.</p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50">
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1">Step 3</span>
              <p className="font-semibold text-slate-700 dark:text-slate-300">Risk Assessment</p>
              <p className="text-slate-500 text-[11px] mt-0.5">0–100 multi-factor capacity scoring.</p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50">
              <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1">Step 4</span>
              <p className="font-semibold text-slate-700 dark:text-slate-300">SEBI Portfolio</p>
              <p className="text-slate-500 text-[11px] mt-0.5">Validated monthly SIP allocations.</p>
            </div>
          </div>

          <div className="pt-2">
            <Link href="/profile">
              <Button size="lg" className="px-8 gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-md">
                Complete Financial Profile
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </Card>
      </main>
    );
  }

  // Calculate Real Financial Metrics from Neon Profile & Backend Analysis
  const netWorth = (profile.total_savings || 0) - (profile.total_debt || 0);
  const monthlySurplus = Math.max(0, (profile.monthly_income || 0) - (profile.monthly_expenses || 0));
  const savingsRatioPct = profile.monthly_income > 0 ? (monthlySurplus / profile.monthly_income) * 100 : 0;
  const emergencyRunwayMonths = profile.monthly_expenses > 0 ? Number(((profile.total_savings || 0) / profile.monthly_expenses).toFixed(1)) : 0;
  const investmentCapacity = profile.monthly_investment_capacity || monthlySurplus;

  const health = analysis?.health ?? {
    monthly_surplus: monthlySurplus,
    savings_ratio_pct: savingsRatioPct,
    emergency_fund_months: emergencyRunwayMonths,
    emergency_fund_target_inr: (profile.monthly_expenses || 0) * 6,
    debt_to_income_ratio: profile.monthly_income > 0 ? (profile.total_debt || 0) / (profile.monthly_income * 12) : 0,
    investment_capacity_inr: investmentCapacity,
    health_status: emergencyRunwayMonths >= 6 ? "HEALTHY" : emergencyRunwayMonths >= 3 ? "MODERATE" : "VULNERABLE",
    flags: [],
  };

  const risk = analysis?.risk ?? {
    risk_score: 50,
    risk_category: (profile.risk_tolerance as any) || "MODERATE",
    tolerance_score: 50,
    capacity_score: 50,
    experience_score: 50,
    time_horizon_score: 50,
    risk_factors: [],
    warnings: [],
  };

  const allocation = analysis?.allocation ?? {
    allocations: [],
    total_monthly_sip: investmentCapacity,
    rationale: "Target asset allocation matrix generated based on your SEBI risk profile.",
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Financial Overview</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Comprehensive health analysis, risk capacity, and multi-asset portfolio status.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/profile">
            <Button size="sm" variant="outline">
              Edit Profile
            </Button>
          </Link>
          <Link href="/advisor">
            <Button size="sm" className="gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white">
              <Sparkles className="w-3.5 h-3.5" />
              Ask AI Advisor
            </Button>
          </Link>
        </div>
      </div>

      {/* Top 4 KPI Metrics (Derived from Neon Profile) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Net Position */}
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Net Financial Position</span>
              <div className="w-7 h-7 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                <Wallet className="w-4 h-4" />
              </div>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-100">{formatINR(netWorth)}</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Savings: <span className="text-slate-200">{formatINR(profile.total_savings || 0)}</span> • Debt: <span className="text-rose-400">{formatINR(profile.total_debt || 0)}</span>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 2. Monthly Surplus & Capacity */}
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Investment Capacity</span>
              <div className="w-7 h-7 rounded bg-sky-500/10 flex items-center justify-center text-sky-400">
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </div>
            <div>
              <p className="text-2xl font-bold text-sky-400">{formatINR(health.investment_capacity_inr)}/mo</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Monthly Surplus: <span className="text-slate-200">{formatINR(health.monthly_surplus)}</span> ({formatPercent(health.savings_ratio_pct)} of income)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 3. Risk Score */}
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Risk Profile</span>
              <Badge variant={risk.risk_category === "MODERATE" ? "blue" : risk.risk_category === "AGGRESSIVE" ? "purple" : "amber"} size="sm">
                {risk.risk_category}
              </Badge>
            </div>
            <div>
              <div className="flex items-baseline gap-1.5">
                <p className="text-2xl font-bold text-slate-100">{risk.risk_score}</p>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
              <Progress value={risk.risk_score} size="sm" indicatorColor="blue" className="mt-2" />
            </div>
          </CardContent>
        </Card>

        {/* 4. Financial Health & Emergency Buffer */}
        <Card>
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Emergency Runway</span>
              <Badge variant={health.emergency_fund_months >= 6 ? "emerald" : "amber"} size="sm">
                {health.health_status}
              </Badge>
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-400">{health.emergency_fund_months} Months</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Target: {formatINR(health.emergency_fund_target_inr)} (6-month buffer)
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Middle Section: Cashflow Breakdown & Asset Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Cashflow Bar Chart */}
        <Card className="lg:col-span-5">
          <CardHeader>
            <CardTitle>Monthly Cashflow Structure</CardTitle>
            <CardDescription>Income vs Expenses vs Investable Surplus</CardDescription>
          </CardHeader>
          <CardContent>
            <MonthlyCashflowChart
              income={profile.monthly_income || 0}
              expenses={profile.monthly_expenses || 0}
              savingsCapacity={health.investment_capacity_inr}
            />
          </CardContent>
        </Card>

        {/* Portfolio Allocation Matrix */}
        <Card className="lg:col-span-7">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>SEBI Target Asset Allocation</CardTitle>
              <CardDescription>Optimized for {risk.risk_category} risk profile</CardDescription>
            </div>
            <Link href="/portfolio">
              <Button size="sm" variant="ghost" className="text-xs text-slate-400 hover:text-slate-100">
                Full Details <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {allocation.allocations.length > 0 ? (
              <AllocationPieChart data={allocation.allocations} />
            ) : (
              <div className="py-12 text-center text-xs text-slate-400">
                Allocation matrix will be rendered after goal and risk evaluation.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section: Active Goals & AI Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Goals Card */}
        <Card className="lg:col-span-6">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-400" />
                Active Financial Goals ({goals.length})
              </CardTitle>
              <CardDescription>Progress towards target corpus amounts</CardDescription>
            </div>
            <Link href="/goals">
              <Button size="sm" variant="outline" className="text-xs">
                Manage Goals
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* STATE B: Profile completed, but no goals */}
            {!hasGoals ? (
              <div className="p-6 text-center rounded-lg bg-slate-800/30 border border-dashed border-slate-700 space-y-3">
                <Target className="w-8 h-8 text-slate-500 mx-auto" />
                <div>
                  <p className="font-semibold text-slate-200 text-xs">No financial goals added yet.</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Add a goal like Retirement or House Downpayment to compute your exact required SIP amounts.
                  </p>
                </div>
                <Link href="/goals">
                  <Button size="sm" className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white">
                    <PlusCircle className="w-3.5 h-3.5" />
                    Create Your First Goal
                  </Button>
                </Link>
              </div>
            ) : (
              goals.slice(0, 3).map((goal, gIdx) => {
                const progressPct = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0;
                return (
                  <div key={goal.id || gIdx} className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-200">
                        {goal.goal_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-slate-400">
                        {formatINR(goal.current_amount)} / {formatINR(goal.target_amount)}
                      </span>
                    </div>
                    <Progress
                      value={progressPct}
                      size="sm"
                      indicatorColor={progressPct >= 75 ? "emerald" : progressPct >= 40 ? "blue" : "amber"}
                    />
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>{progressPct}% Funded</span>
                      <span>Target: {goal.target_years} {goal.target_years === 1 ? "Year" : "Years"}</span>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        {/* AI Insight & Recommendations Card */}
        <Card className="lg:col-span-6 border-emerald-500/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-emerald-400">
                <Sparkles className="w-4 h-4" />
                AI &amp; Mathematical Recommendation
              </CardTitle>
              <Badge variant={hasRecommendation ? "emerald" : "slate"} size="sm">
                {hasRecommendation ? "Generated & Saved" : "Action Required"}
              </Badge>
            </div>
            <CardDescription>Deterministic Portfolio Synthesis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3.5">
            {/* STATE B & C: No recommendation generated yet */}
            {!hasRecommendation ? (
              <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-3 text-xs">
                {!hasGoals ? (
                  <p className="text-slate-300 leading-relaxed">
                    Please add at least one financial goal to unlock your personalized SEBI portfolio recommendation.
                  </p>
                ) : (
                  <p className="text-slate-300 leading-relaxed">
                    Your profile and goals are ready! Generate your official recommendation to construct a validated portfolio across equities, debt, gold, and cash.
                  </p>
                )}

                <div className="pt-1 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    Monthly Investment Capacity: <strong className="text-emerald-400">{formatINR(health.investment_capacity_inr)}</strong>
                  </span>

                  {hasGoals ? (
                    <Button
                      size="sm"
                      onClick={handleGenerate}
                      isLoading={isGenerating}
                      className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Generate Recommendation
                    </Button>
                  ) : (
                    <Link href="/goals">
                      <Button size="sm" variant="outline" className="text-xs">
                        Add Goal First
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            ) : (
              /* STATE D: Recommendation Generated */
              <>
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-slate-200 leading-relaxed">
                  <p className="font-semibold text-emerald-300 mb-1">Portfolio Strategy Rationale:</p>
                  {allocation.rationale}
                </div>

                <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-xs flex items-center justify-between text-slate-300">
                  <span>Selected Instruments:</span>
                  <span className="font-semibold text-white">
                    {recommendation?.portfolio_items?.length || 0} SEBI-Approved Products
                  </span>
                </div>

                <div className="pt-2 flex items-center justify-between">
                  <span className="text-xs text-slate-400">
                    Total Recommended Monthly SIP: <strong className="text-slate-100">{formatINR(allocation.total_monthly_sip)}</strong>
                  </span>
                  <Link href="/recommendations">
                    <Button size="sm" className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white">
                      View Full Report <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </Link>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
