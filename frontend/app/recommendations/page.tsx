"use client";

import React from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useFinancialData } from "@/hooks/useFinancialData";
import { formatINR, formatPercent } from "@/lib/utils";
import {
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  TrendingUp,
  FileCheck,
  AlertCircle,
  Clock,
} from "lucide-react";

export default function RecommendationsPage() {
  const { analysis, profile, goals } = useFinancialData();
  const { allocation, risk, health, goals_feasibility } = analysis;

  return (
    <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
      <Sidebar />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        {/* Header with Timestamp */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileCheck className="w-6 h-6 text-emerald-400" />
              Official Financial Recommendation Report
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic asset synthesis aligned with SEBI risk-profile bounds and Indian Income Tax codes.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant="emerald" size="md">
              <Clock className="w-3 h-3 mr-1" />
              Generated: {new Date(analysis.analyzed_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
            </Badge>
          </div>
        </div>

        {/* Executive Summary Card */}
        <Card className="bg-gradient-to-r from-emerald-950/30 via-slate-900 to-slate-900 border-emerald-500/30">
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Executive Synthesis
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Profile: {risk.risk_category} ({risk.risk_score}/100)
              </span>
            </div>

            <p className="text-sm text-slate-200 leading-relaxed">
              {allocation.rationale}
            </p>

            <div className="pt-2 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-slate-800/80 text-xs">
              <div>
                <span className="text-slate-400">Total Monthly SIP:</span>
                <p className="text-base font-bold text-emerald-400">{formatINR(allocation.total_monthly_sip)}</p>
              </div>
              <div>
                <span className="text-slate-400">Emergency Runway:</span>
                <p className="text-base font-bold text-sky-400">{health.emergency_fund_months} Months</p>
              </div>
              <div>
                <span className="text-slate-400">Target Equity Exposure:</span>
                <p className="text-base font-bold text-slate-100">{allocation.allocations.find(a => a.asset_class === 'equity')?.target_pct}%</p>
              </div>
              <div>
                <span className="text-slate-400">Active Goals Tracked:</span>
                <p className="text-base font-bold text-purple-400">{goals.length} Goals</p>
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
            <CardDescription>Exact SIP amounts by asset class and suggested vehicle mandates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-slate-800/80">
              {allocation.allocations.map((item) => (
                <div key={item.asset_class} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1 md:w-1/3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-100 uppercase text-sm">{item.asset_class}</span>
                      <Badge
                        variant={
                          item.asset_class === "equity"
                            ? "emerald"
                            : item.asset_class === "debt"
                            ? "blue"
                            : item.asset_class === "gold"
                            ? "amber"
                            : "slate"
                        }
                        size="sm"
                      >
                        {item.target_pct}% Weight
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400">
                      Permissible Range: {item.min_pct}% – {item.max_pct}%
                    </p>
                  </div>

                  <div className="md:w-1/3">
                    <span className="text-xs text-slate-400">Recommended Monthly SIP</span>
                    <p className="text-lg font-extrabold text-emerald-400">{formatINR(item.monthly_sip_inr)}/mo</p>
                  </div>

                  <div className="md:w-1/3 text-xs space-y-1">
                    <span className="text-slate-400 font-semibold">Recommended Vehicles:</span>
                    {item.suggested_instruments.map((inst, i) => (
                      <p key={i} className="text-slate-300 text-[11px]">• {inst}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Goal Alignment & Feasibility Roadmap */}
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
              {goals_feasibility.map((gf, idx) => (
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
                  <span>Reserve Bank of India & DICGC Guidelines</span>
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
    </div>
  );
}
