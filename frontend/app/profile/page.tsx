"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { UserProfile, RiskTolerance, InvestmentExperience } from "@/types";
import { formatINR } from "@/lib/utils";
import { User, Wallet, ShieldAlert, Sparkles } from "lucide-react";

const DEFAULT_PROFILE_STATE: UserProfile = {
  age: 30,
  monthly_income: 100000,
  monthly_expenses: 50000,
  total_savings: 200000,
  monthly_investment_capacity: 40000,
  total_debt: 0,
  risk_tolerance: "MODERATE",
  investment_experience: "INTERMEDIATE",
};

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <Sidebar />

        <ProfileContent />
      </div>
    </ProtectedRoute>
  );
}

function ProfileContent() {
  const { profile, updateProfile, analysis } = useFinancialData();

  const [formData, setFormData] = useState<UserProfile>(profile || DEFAULT_PROFILE_STATE);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (profile) {
      setFormData(profile);
    }
  }, [profile]);

  const handleChange = (field: keyof UserProfile, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const calculatedSurplus = Math.max(0, (formData.monthly_income || 0) - (formData.monthly_expenses || 0));
  const calculatedRunway =
    formData.monthly_expenses > 0
      ? ((formData.total_savings || 0) / formData.monthly_expenses).toFixed(1)
      : "0";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await updateProfile(formData);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Financial Profile Assessment</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Enter your income, expenses, and investment preferences to generate your risk profile and SEBI asset matrix.
          </p>
        </div>
        <Badge variant="emerald" size="md">
          Currency: INR (₹)
        </Badge>
      </div>

      {/* Live Calculation Preview Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-900/90 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 font-bold text-sm">
            ₹
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium">Calculated Monthly Surplus</p>
            <p className="text-base font-bold text-emerald-400">{formatINR(calculatedSurplus)}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 font-bold text-sm">
            ⏳
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium">Liquid Emergency Runway</p>
            <p className="text-base font-bold text-sky-400">{calculatedRunway} Months</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 font-bold text-sm">
            🎯
          </div>
          <div>
            <p className="text-[11px] text-slate-400 font-medium">Current Risk Category</p>
            <p className="text-base font-bold text-amber-400">{analysis?.risk?.risk_category || formData.risk_tolerance}</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Demographics & Cash Flow */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-4 h-4 text-emerald-400" />
              1. Monthly Cashflow & Demographics
            </CardTitle>
            <CardDescription>Your personal profile and monthly inflows / outflows</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Age (Years)"
              type="number"
              min={18}
              max={100}
              value={formData.age}
              onChange={(e) => handleChange("age", parseInt(e.target.value) || 0)}
              required
            />

            <Input
              label="Monthly Income (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              value={formData.monthly_income}
              onChange={(e) => handleChange("monthly_income", parseFloat(e.target.value) || 0)}
              required
            />

            <Input
              label="Monthly Expenses (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              value={formData.monthly_expenses}
              onChange={(e) => handleChange("monthly_expenses", parseFloat(e.target.value) || 0)}
              required
            />
          </CardContent>
        </Card>

        {/* Section 2: Assets, Liabilities & Capacity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="w-4 h-4 text-sky-400" />
              2. Wealth Base & Investment Capacity
            </CardTitle>
            <CardDescription>Liquid savings, current liabilities, and target monthly SIP</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Total Liquid Savings (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={5000}
              value={formData.total_savings}
              onChange={(e) => handleChange("total_savings", parseFloat(e.target.value) || 0)}
              helperText="Bank balances, liquid mutual funds, FDs"
              required
            />

            <Input
              label="Total Outstanding Debt (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={5000}
              value={formData.total_debt}
              onChange={(e) => handleChange("total_debt", parseFloat(e.target.value) || 0)}
              helperText="Personal loans, credit card balances, vehicle loans"
              required
            />

            <Input
              label="Target Monthly Investment (SIP)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              value={formData.monthly_investment_capacity}
              onChange={(e) => handleChange("monthly_investment_capacity", parseFloat(e.target.value) || 0)}
              helperText="Recommended: <= Monthly Surplus"
              required
            />
          </CardContent>
        </Card>

        {/* Section 3: Risk Tolerance & Market Experience */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-purple-400" />
              3. Risk Tolerance & Market Experience
            </CardTitle>
            <CardDescription>Determines your willingness to withstand equity market drawdowns</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Self-Declared Risk Tolerance"
              value={formData.risk_tolerance}
              onChange={(e) => handleChange("risk_tolerance", e.target.value as RiskTolerance)}
              options={[
                { value: "CONSERVATIVE", label: "Conservative (Capital preservation, low volatility)" },
                { value: "MODERATE", label: "Moderate (Balanced equity & fixed income growth)" },
                { value: "AGGRESSIVE", label: "Aggressive (High equity allocation, maximum compounding)" },
              ]}
              helperText="Weight in risk scoring algorithm: 25%"
            />

            <Select
              label="Investment Market Experience"
              value={formData.investment_experience}
              onChange={(e) => handleChange("investment_experience", e.target.value as InvestmentExperience)}
              options={[
                { value: "BEGINNER", label: "Beginner (< 2 years, primarily FDs and savings)" },
                { value: "INTERMEDIATE", label: "Intermediate (2-5 years, active SIPs and mutual funds)" },
                { value: "ADVANCED", label: "Advanced (> 5 years, direct equities, bonds, derivatives)" },
              ]}
              helperText="Weight in risk scoring algorithm: 15%"
            />
          </CardContent>
          <CardFooter className="flex justify-between items-center">
            <span className="text-xs text-slate-400">
              All changes automatically trigger deterministic SEBI asset re-simulation.
            </span>
            <Button type="submit" isLoading={isSaving} className="gap-2">
              <Sparkles className="w-4 h-4" />
              Save & Recalculate
            </Button>
          </CardFooter>
        </Card>
      </form>
    </main>
  );
}
