"use client";

import React from "react";
import Link from "next/link";
import {
  Wallet,
  ArrowUpRight,
  Target,
  Sparkles,
  AlertTriangle,
  ChevronRight,
} from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { AllocationPieChart } from "@/components/charts/AllocationPieChart";
import { MonthlyCashflowChart } from "@/components/charts/MonthlyCashflowChart";
import { Skeleton } from "@/components/ui/Skeleton";
import { useFinancialData } from "@/hooks/useFinancialData";
import { formatINR, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { profile, goals, analysis, isLoading } = useFinancialData();

  const netWorth = (profile?.total_savings ?? 0) - (profile?.total_debt ?? 0);
  const health = analysis?.health ?? {
    monthly_surplus: 0,
    savings_ratio_pct: 0,
    emergency_fund_months: 0,
    emergency_fund_target_inr: 0,
    debt_to_income_ratio: 0,
    investment_capacity_inr: 0,
    health_status: "HEALTHY",
    flags: [],
  };

  const risk = analysis?.risk ?? {
    risk_score: 50,
    risk_category: "MODERATE",
    tolerance_score: 50,
    capacity_score: 50,
    experience_score: 50,
    time_horizon_score: 50,
    risk_factors: [],
    warnings: [],
  };

  const allocation = analysis?.allocation ?? {
    allocations: [],
    total_monthly_sip: 0,
    rationale: "",
  };

  return (
    <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Financial Overview</h1>
            <p className="text-xs text-slate-400 mt-0.5">
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
              <Button size="sm" className="gap-1.5 bg-emerald-600 hover:bg-emerald-500">
                <Sparkles className="w-3.5 h-3.5 text-white" />
                Ask AI Advisor
              </Button>
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
        ) : (
          /* Top 4 KPI Metrics */
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
                    Savings: <span className="text-slate-200">{formatINR(profile?.total_savings ?? 0)}</span> • Debt: <span className="text-rose-400">{formatINR(profile?.total_debt ?? 0)}</span>
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
                  <Badge variant="emerald" size="sm">
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
        )}

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
                income={profile?.monthly_income ?? 0}
                expenses={profile?.monthly_expenses ?? 0}
                savingsCapacity={health.investment_capacity_inr}
              />
            </CardContent>
          </Card>

          {/* Portfolio Allocation Matrix */}
          <Card className="lg:col-span-7">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>SEBI Target Asset Allocation</CardTitle>
                <CardDescription>Optimized for {risk.risk_category} risk & goals</CardDescription>
              </div>
              <Link href="/portfolio">
                <Button size="sm" variant="ghost" className="text-xs text-slate-400 hover:text-slate-100">
                  Full Details <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              <AllocationPieChart data={allocation.allocations} />
            </CardContent>
          </Card>
        </div>

        {/* Bottom Section: Active Goals & Recent AI Recommendation */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Active Goals Card */}
          <Card className="lg:col-span-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-4 h-4 text-emerald-400" />
                  Active Financial Goals ({(goals ?? []).length})
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
              {(goals ?? []).slice(0, 3).map((goal, gIdx) => {
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
              })}
            </CardContent>
          </Card>

          {/* AI Insight & Recommendations Card */}
          <Card className="lg:col-span-6 border-emerald-500/30">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-emerald-400">
                  <Sparkles className="w-4 h-4" />
                  AI & Mathematical Insights
                </CardTitle>
                <Badge variant="emerald" size="sm">Rule-Validated</Badge>
              </div>
              <CardDescription>Deterministic Rationale & Key Considerations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3.5">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-slate-200 leading-relaxed">
                <p className="font-semibold text-emerald-300 mb-1">Portfolio Strategy Rationale:</p>
                {allocation.rationale}
              </div>

              {(risk?.warnings ?? []).length > 0 && (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 leading-relaxed flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-amber-300">Risk Notice:</p>
                    <p className="text-[11px] text-amber-200/90 mt-0.5">{risk.warnings[0]}</p>
                  </div>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Total Recommended Monthly SIP: <strong className="text-slate-100">{formatINR(allocation.total_monthly_sip)}</strong>
                </span>
                <Link href="/recommendations">
                  <Button size="sm" variant="primary" className="text-xs">
                    View Full Roadmap
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
