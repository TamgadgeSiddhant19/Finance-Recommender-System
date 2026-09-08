"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { AllocationPieChart } from "@/components/charts/AllocationPieChart";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { productsService } from "@/services/productsService";
import { FinancialProduct } from "@/types";
import { formatINR } from "@/lib/utils";
import { PieChart as PieIcon, Layers, UserPlus } from "lucide-react";

export default function PortfolioPage() {
  return (
    <ProtectedRoute>
      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <Sidebar />

        <PortfolioContent />
      </div>
    </ProtectedRoute>
  );
}

function PortfolioContent() {
  const { analysis, profile, hasProfile, isLoading } = useFinancialData();
  const [products, setProducts] = useState<FinancialProduct[]>([]);
  const [selectedAssetFilter, setSelectedAssetFilter] = useState<string>("all");

  useEffect(() => {
    async function loadCatalog() {
      try {
        const res = await productsService.getProducts();
        setProducts(Array.isArray(res) ? res : []);
      } catch (err) {
        setProducts([]);
      }
    }
    loadCatalog();
  }, []);

  if (isLoading) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-80 w-full rounded-xl" />
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
              To calculate your target multi-asset allocation matrix and SIP deployment breakdown, please configure your financial profile.
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

  const safeProducts = Array.isArray(products) ? products : [];
  const filteredProducts =
    selectedAssetFilter === "all"
      ? safeProducts
      : safeProducts.filter((p) => p.asset_class?.toLowerCase() === selectedAssetFilter.toLowerCase());

  const allocation = analysis?.allocation ?? {
    allocations: [],
    total_monthly_sip: profile.monthly_investment_capacity || 0,
    rationale: "Default balanced allocation.",
  };

  const riskCategory = analysis?.risk?.risk_category || profile.risk_tolerance || "MODERATE";

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Target Portfolio Allocation Matrix</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            SEBI-aligned multi-asset framework balanced across Equities, Debt, Gold, and Liquid Cash.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Total Recommended Monthly SIP: <strong className="text-emerald-700 dark:text-emerald-400 font-bold">{formatINR(allocation.total_monthly_sip)}</strong>
          </span>
          <Link href="/recommendations">
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white">
              View Advice Report
            </Button>
          </Link>
        </div>
      </div>

      {/* Top Section: Donut Chart & Allocation Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-emerald-400" />
            Target Weights & Monthly Capital Deployment
          </CardTitle>
          <CardDescription>
            Balanced allocation for {riskCategory} risk profile with {formatINR(allocation.total_monthly_sip)}/mo capacity
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AllocationPieChart data={allocation.allocations} />
        </CardContent>
      </Card>

      {/* Detailed Allocation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {allocation.allocations.map((item) => {
          const colors: Record<string, string> = {
            equity: "border-emerald-500/30 bg-emerald-500/5",
            debt: "border-sky-500/30 bg-sky-500/5",
            gold: "border-amber-500/30 bg-amber-500/5",
            cash: "border-slate-700 bg-slate-800/30",
          };

          const badges: Record<string, "emerald" | "blue" | "amber" | "slate"> = {
            equity: "emerald",
            debt: "blue",
            gold: "amber",
            cash: "slate",
          };

          return (
            <Card key={item.asset_class} className={`p-4 ${colors[item.asset_class] || colors.cash}`}>
              <div className="flex items-center justify-between">
                <Badge variant={badges[item.asset_class] || "slate"} size="sm">
                  {item.asset_class.toUpperCase()}
                </Badge>
                <span className="text-base font-extrabold text-slate-100">{item.target_pct}%</span>
              </div>

              <div className="mt-3">
                <span className="text-[11px] text-slate-400">Monthly SIP Contribution</span>
                <p className="text-lg font-bold text-slate-100">{formatINR(item.monthly_sip_inr)}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Range: {item.min_pct}% – {item.max_pct}%
                </p>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/40 text-[11px] space-y-1">
                <p className="font-semibold text-slate-300">Suggested Vehicles:</p>
                {(item.suggested_instruments || []).map((inst, idx) => (
                  <p key={idx} className="text-slate-400 truncate">• {inst}</p>
                ))}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Filterable Products & Instruments Catalog */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              Verified Indian Financial Instruments Catalog
            </CardTitle>
            <CardDescription>Available products meeting SEBI & RBI regulatory standards</CardDescription>
          </div>

          {/* Asset Class Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
            {["all", "equity", "debt", "gold", "cash"].map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedAssetFilter(tab)}
                className={`px-3 py-1 rounded-md capitalize font-medium transition-colors cursor-pointer ${
                  selectedAssetFilter === tab
                    ? "bg-emerald-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-slate-800/60">
            {filteredProducts.map((p) => (
              <div key={p.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-100 text-sm">{p.name}</span>
                    <Badge
                      variant={
                        p.asset_class === "equity"
                          ? "emerald"
                          : p.asset_class === "debt"
                          ? "blue"
                          : p.asset_class === "gold"
                          ? "amber"
                          : "slate"
                      }
                      size="sm"
                    >
                      {p.product_type.replace(/_/g, " ")}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                    <span>Symbol: <strong className="text-slate-300">{p.symbol}</strong></span>
                    <span>Issuer: <strong className="text-slate-300">{p.issuer}</strong></span>
                    <span>Risk: <strong className="text-slate-300 uppercase">{p.risk_level.replace(/_/g, " ")}</strong></span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs text-slate-400">Expense Ratio</span>
                  <p className="text-sm font-bold text-slate-200">
                    {p.expense_ratio !== undefined && p.expense_ratio > 0 ? `${p.expense_ratio}%` : "0.0%"}
                  </p>
                  <span className="text-[10px] text-slate-400">Min: {formatINR(p.minimum_investment || 500)}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
