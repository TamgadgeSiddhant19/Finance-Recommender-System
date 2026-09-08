"use client";

import React from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { Skeleton } from "@/components/ui/Skeleton";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { ShieldCheck, AlertTriangle, ArrowRight, Gauge, CheckCircle2, UserPlus } from "lucide-react";
import { formatINR, formatPercent } from "@/lib/utils";

export default function RiskAssessmentPage() {
  return (
    <ProtectedRoute>
      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <Sidebar />

        <RiskContent />
      </div>
    </ProtectedRoute>
  );
}

function RiskContent() {
  const { analysis, profile, hasProfile, isLoading } = useFinancialData();

  if (isLoading) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Skeleton className="lg:col-span-5 h-80 rounded-xl" />
          <Skeleton className="lg:col-span-7 h-80 rounded-xl" />
        </div>
      </main>
    );
  }

  if (!hasProfile || !profile) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-2xl mx-auto space-y-6 flex flex-col justify-center">
        <Card className="p-8 text-center space-y-4 border-emerald-500/30 bg-slate-900/60">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Financial Profile Required</h3>
            <p className="text-xs text-slate-300 max-w-md mx-auto mt-1">
              To calculate your deterministic 0–100 risk score and SEBI allocation guardrails, please set up your financial profile.
            </p>
          </div>
          <Link href="/profile">
            <Button className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white">
              Create Financial Profile
            </Button>
          </Link>
        </Card>
      </main>
    );
  }

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

  const health = analysis?.health ?? {
    monthly_surplus: Math.max(0, profile.monthly_income - profile.monthly_expenses),
    savings_ratio_pct: profile.monthly_income > 0 ? ((profile.monthly_income - profile.monthly_expenses) / profile.monthly_income) * 100 : 0,
    emergency_fund_months: profile.monthly_expenses > 0 ? Number((profile.total_savings / profile.monthly_expenses).toFixed(1)) : 0,
    emergency_fund_target_inr: profile.monthly_expenses * 6,
    debt_to_income_ratio: profile.monthly_income > 0 ? profile.total_debt / (profile.monthly_income * 12) : 0,
    investment_capacity_inr: profile.monthly_investment_capacity || Math.max(0, profile.monthly_income - profile.monthly_expenses),
    health_status: "HEALTHY",
    flags: [],
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Multi-Factor Risk Assessment</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Deterministic 0–100 scoring based on capacity, liquid runway, self-declared tolerance, and investment horizon.
          </p>
        </div>

        <Link href="/recommendations">
          <Button size="sm" className="gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white">
            View Aligned Portfolio <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>

      {/* Hero Score Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Score Gauge */}
        <Card className="lg:col-span-5 flex flex-col justify-center items-center text-center p-8 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 border-emerald-500/30">
          <div className="relative flex items-center justify-center mb-4">
            <div className="w-44 h-44 rounded-full border-4 border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center p-4 bg-white dark:bg-slate-950/80 shadow-inner">
              <span className="text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {risk.risk_score}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-1">/ 100 Score</span>
              <Badge
                variant={
                  risk.risk_category === "CONSERVATIVE"
                    ? "amber"
                    : risk.risk_category === "MODERATE"
                    ? "blue"
                    : "purple"
                }
                size="sm"
                className="mt-2"
              >
                {risk.risk_category}
              </Badge>
            </div>
          </div>

          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {risk.risk_category} Risk Category
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed max-w-xs">
            Balanced tolerance for equity market cycles, anchored by liquid cash buffers and institutional debt allocations.
          </p>
        </Card>

        {/* 4 Factor Component Breakdown */}
        <Card className="lg:col-span-7">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-emerald-400" />
              Underlying Score Dimensions (Weighted Matrix)
            </CardTitle>
            <CardDescription>Mathematical factors shaping your asset allocation boundary</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 1. Risk Capacity */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-300">Financial Capacity (Weight: 35%)</span>
                <span className="font-bold text-emerald-400">{risk.capacity_score} / 100</span>
              </div>
              <Progress value={risk.capacity_score} indicatorColor="emerald" />
              <p className="text-[11px] text-slate-400">
                Derived from debt-to-income ratio ({profile.total_debt === 0 ? "0%" : formatINR(profile.total_debt)} debt) and monthly surplus headroom.
              </p>
            </div>

            {/* 2. Self-Declared Tolerance */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-300">Stated Tolerance (Weight: 25%)</span>
                <span className="font-bold text-sky-400">{risk.tolerance_score} / 100</span>
              </div>
              <Progress value={risk.tolerance_score} indicatorColor="blue" />
              <p className="text-[11px] text-slate-400">
                Reflects willingness to absorb interim drawdown for compounding ({profile.risk_tolerance}).
              </p>
            </div>

            {/* 3. Time Horizon */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-300">Time Horizon Factor (Weight: 25%)</span>
                <span className="font-bold text-purple-400">{risk.time_horizon_score} / 100</span>
              </div>
              <Progress value={risk.time_horizon_score} indicatorColor="purple" />
              <p className="text-[11px] text-slate-400">
                Calculated from age ({profile.age} years) and weighted goal duration.
              </p>
            </div>

            {/* 4. Investment Experience */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-300">Market Experience (Weight: 15%)</span>
                <span className="font-bold text-amber-400">{risk.experience_score} / 100</span>
              </div>
              <Progress value={risk.experience_score} indicatorColor="amber" />
              <p className="text-[11px] text-slate-400">
                Familiarity with market cycles ({profile.investment_experience}).
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Health Buffer & Strategic Warnings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Health Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              Financial Health & Resilience
            </CardTitle>
            <CardDescription>Emergency runway and balance sheet indicators</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40">
              <span className="text-slate-400">Liquid Runway:</span>
              <span className="font-bold text-emerald-400">{health.emergency_fund_months} Months of Expenses</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40">
              <span className="text-slate-400">Savings Ratio:</span>
              <span className="font-bold text-slate-100">{formatPercent(health.savings_ratio_pct)} of Net Income</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/40">
              <span className="text-slate-400">Debt-to-Income:</span>
              <span className="font-bold text-slate-100">{(health.debt_to_income_ratio * 100).toFixed(1)}%</span>
            </div>

            <div className="pt-2 space-y-1.5">
              {(health.flags || []).map((flag, idx) => (
                <div key={idx} className="flex items-start gap-2 text-slate-300 text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Strategic Warnings & Guardrails */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
              SEBI Asset Allocation Guardrails
            </CardTitle>
            <CardDescription>Rules preventing over-exposure and portfolio drift</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200/90 leading-relaxed">
              <p className="font-semibold text-amber-300 mb-1">Downside Protection Mandate:</p>
              For {risk.risk_category} profiles, equity allocation is strictly bounded by deterministic rules to control volatility and drawdown risk.
            </div>

            {(risk.warnings || []).map((warn, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-300 text-[11px] leading-relaxed">
                <strong className="text-slate-100">Horizon Transition:</strong> {warn}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
