"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { RiskTolerance, InvestmentExperience } from "@/types";
import { formatINR } from "@/lib/utils";
import { User, Wallet, ShieldAlert, Sparkles, CheckCircle2 } from "lucide-react";

interface ProfileFormState {
  age: string | number;
  monthly_income: string | number;
  monthly_expenses: string | number;
  total_savings: string | number;
  monthly_investment_capacity: string | number;
  total_debt: string | number;
  risk_tolerance: RiskTolerance | "";
  investment_experience: InvestmentExperience | "";
}

const EMPTY_FORM_STATE: ProfileFormState = {
  age: "",
  monthly_income: "",
  monthly_expenses: "",
  total_savings: "",
  monthly_investment_capacity: "",
  total_debt: "0",
  risk_tolerance: "",
  investment_experience: "",
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
  const { profile, updateProfile, analysis, hasProfile, isLoading } = useFinancialData();

  const [formData, setFormData] = useState<ProfileFormState>(EMPTY_FORM_STATE);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      setFormData({
        age: profile.age ?? "",
        monthly_income: profile.monthly_income ?? "",
        monthly_expenses: profile.monthly_expenses ?? "",
        total_savings: profile.total_savings ?? "",
        monthly_investment_capacity: profile.monthly_investment_capacity ?? "",
        total_debt: profile.total_debt ?? "0",
        risk_tolerance: profile.risk_tolerance || "",
        investment_experience: profile.investment_experience || "",
      });
    } else {
      setFormData(EMPTY_FORM_STATE);
    }
  }, [profile]);

  if (isLoading) {
    return (
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </main>
    );
  }

  const handleChange = (field: keyof ProfileFormState, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    setFormError(null);
  };

  const numIncome = parseFloat(String(formData.monthly_income)) || 0;
  const numExpenses = parseFloat(String(formData.monthly_expenses)) || 0;
  const numSavings = parseFloat(String(formData.total_savings)) || 0;
  const numDebt = parseFloat(String(formData.total_debt)) || 0;
  const numCapacity = parseFloat(String(formData.monthly_investment_capacity)) || 0;

  const hasCashflowInput = numIncome > 0 && numExpenses > 0;
  const calculatedSurplus = Math.max(0, numIncome - numExpenses);
  const calculatedRunway = numExpenses > 0 ? (numSavings / numExpenses).toFixed(1) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const parsedAge = parseInt(String(formData.age));
    if (isNaN(parsedAge) || parsedAge < 18 || parsedAge > 100) {
      setFormError("Please enter a valid age between 18 and 100.");
      return;
    }

    if (numIncome <= 0) {
      setFormError("Monthly income must be greater than ₹0.");
      return;
    }

    if (numExpenses < 0) {
      setFormError("Monthly expenses cannot be negative.");
      return;
    }

    if (numExpenses > numIncome) {
      setFormError("Monthly expenses cannot exceed total monthly income.");
      return;
    }

    if (!formData.risk_tolerance) {
      setFormError("Please select your risk tolerance category.");
      return;
    }

    if (!formData.investment_experience) {
      setFormError("Please select your investment market experience.");
      return;
    }

    const payload = {
      age: parsedAge,
      monthly_income: numIncome,
      monthly_expenses: numExpenses,
      total_savings: numSavings,
      monthly_investment_capacity: numCapacity > 0 ? numCapacity : calculatedSurplus,
      total_debt: numDebt,
      risk_tolerance: formData.risk_tolerance as RiskTolerance,
      investment_experience: formData.investment_experience as InvestmentExperience,
    };

    setIsSaving(true);
    try {
      await updateProfile(payload);
    } catch (err: any) {
      setFormError(err.message || "Failed to save profile. Please check your inputs.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Financial Profile Assessment</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {hasProfile
              ? "Update your income, liabilities, and risk tolerance to recalculate your metrics."
              : "Welcome! Fill in your financial details to build your profile and calculate SEBI metrics."}
          </p>
        </div>
        <Badge variant={hasProfile ? "emerald" : "amber"} size="md">
          {hasProfile ? "Profile Active (Neon DB)" : "New User — Profile Incomplete"}
        </Badge>
      </div>

      {/* Live Calculation Preview Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-xs dark:shadow-none">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-50/60 dark:bg-transparent border border-emerald-100 dark:border-transparent">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center text-emerald-700 dark:text-emerald-400 font-bold text-sm">
            ₹
          </div>
          <div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Calculated Monthly Surplus</p>
            <p className="text-base font-bold text-emerald-700 dark:text-emerald-400">
              {hasCashflowInput ? formatINR(calculatedSurplus) : "—"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-sky-50/60 dark:bg-transparent border border-sky-100 dark:border-transparent">
          <div className="w-8 h-8 rounded-lg bg-sky-500/15 flex items-center justify-center text-sky-700 dark:text-sky-400 font-bold text-sm">
            ⏳
          </div>
          <div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Liquid Emergency Runway</p>
            <p className="text-base font-bold text-sky-700 dark:text-sky-400">
              {calculatedRunway !== null ? `${calculatedRunway} Months` : "—"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-amber-50/60 dark:bg-transparent border border-amber-100 dark:border-transparent">
          <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center text-amber-800 dark:text-amber-400 font-bold text-sm">
            🎯
          </div>
          <div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Risk Category</p>
            <p className="text-base font-bold text-amber-800 dark:text-amber-400">
              {hasProfile && (profile?.risk_tolerance || analysis?.risk?.risk_category)
                ? (analysis?.risk?.risk_category || profile?.risk_tolerance)
                : (formData.risk_tolerance || "—")}
            </p>
          </div>
        </div>
      </div>

      {formError && (
        <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {formError}
        </div>
      )}

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
              placeholder="e.g. 28"
              value={formData.age}
              onChange={(e) => handleChange("age", e.target.value)}
              required
            />

            <Input
              label="Monthly Income (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              placeholder="e.g. 85000"
              value={formData.monthly_income}
              onChange={(e) => handleChange("monthly_income", e.target.value)}
              required
            />

            <Input
              label="Monthly Expenses (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              placeholder="e.g. 40000"
              value={formData.monthly_expenses}
              onChange={(e) => handleChange("monthly_expenses", e.target.value)}
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
              placeholder="e.g. 150000"
              value={formData.total_savings}
              onChange={(e) => handleChange("total_savings", e.target.value)}
              helperText="Bank balances, liquid mutual funds, FDs"
              required
            />

            <Input
              label="Total Outstanding Debt (INR)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={5000}
              placeholder="e.g. 0"
              value={formData.total_debt}
              onChange={(e) => handleChange("total_debt", e.target.value)}
              helperText="Personal loans, credit card balances, vehicle loans"
              required
            />

            <Input
              label="Target Monthly Investment (SIP)"
              type="number"
              prefixSymbol="₹"
              min={0}
              step={1000}
              placeholder={hasCashflowInput ? `Max: ₹${calculatedSurplus}` : "e.g. 25000"}
              value={formData.monthly_investment_capacity}
              onChange={(e) => handleChange("monthly_investment_capacity", e.target.value)}
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
                { value: "", label: "-- Select Risk Tolerance --" },
                { value: "CONSERVATIVE", label: "Conservative (Capital preservation, low volatility)" },
                { value: "MODERATE", label: "Moderate (Balanced equity & fixed income growth)" },
                { value: "AGGRESSIVE", label: "Aggressive (High equity allocation, maximum compounding)" },
              ]}
              helperText="Weight in risk scoring algorithm: 25%"
              required
            />

            <Select
              label="Investment Market Experience"
              value={formData.investment_experience}
              onChange={(e) => handleChange("investment_experience", e.target.value as InvestmentExperience)}
              options={[
                { value: "", label: "-- Select Market Experience --" },
                { value: "BEGINNER", label: "Beginner (< 2 years, primarily FDs and savings)" },
                { value: "INTERMEDIATE", label: "Intermediate (2-5 years, active SIPs and mutual funds)" },
                { value: "ADVANCED", label: "Advanced (> 5 years, direct equities, bonds, derivatives)" },
              ]}
              helperText="Weight in risk scoring algorithm: 15%"
              required
            />
          </CardContent>
          <CardFooter className="flex justify-between items-center">
            <span className="text-xs text-slate-400">
              All data is saved securely to your Neon PostgreSQL database.
            </span>
            <Button type="submit" isLoading={isSaving} className="gap-2">
              <Sparkles className="w-4 h-4" />
              {hasProfile ? "Update Financial Profile" : "Save Profile & Calculate"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </main>
  );
}
