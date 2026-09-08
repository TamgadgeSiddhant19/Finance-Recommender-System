"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { Progress } from "@/components/ui/Progress";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useFinancialData } from "@/hooks/useFinancialData";
import { GoalType, GoalPriority } from "@/types";
import { formatINR } from "@/lib/utils";
import { Target, Plus, ShieldCheck, Clock, X, Sparkles } from "lucide-react";

export default function GoalsPage() {
  return (
    <ProtectedRoute>
      <div className="flex-1 flex min-h-[calc(100vh-4rem)]">
        <Sidebar />

        <GoalsContent />
      </div>
    </ProtectedRoute>
  );
}

function GoalsContent() {
  const { goals, addGoal, analysis } = useFinancialData();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [newGoal, setNewGoal] = useState<{
    goal_type: GoalType;
    target_amount: number;
    current_amount: number;
    target_years: number;
    priority: GoalPriority;
  }>({
    goal_type: "RETIREMENT",
    target_amount: 10000000,
    current_amount: 500000,
    target_years: 15,
    priority: "HIGH",
  });

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await addGoal(newGoal);
      setIsModalOpen(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Financial Goals & Compounding Roadmap</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Track progress, required SIP amounts, and feasibility calculations for your life goals.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="gap-2 bg-emerald-600 hover:bg-emerald-500 text-white">
          <Plus className="w-4 h-4" /> Add Financial Goal
        </Button>
      </div>

      {/* If No Goals */}
      {goals.length === 0 ? (
        <Card className="p-8 text-center space-y-4 border-dashed border-slate-700 bg-slate-900/40">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">No Financial Goals Added Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Add goals such as Retirement, House Downpayment, Emergency Fund, or Higher Education to calculate required monthly SIP amounts.
            </p>
          </div>
          <Button onClick={() => setIsModalOpen(true)} className="gap-2">
            <Plus className="w-4 h-4" /> Create First Goal
          </Button>
        </Card>
      ) : (
        /* Goals Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {goals.map((goal, idx) => {
            const progressPct = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0;
            const feasibility = analysis?.goals_feasibility?.find((g) => g.goal_type === goal.goal_type);

            return (
              <Card key={goal.id || idx} className="flex flex-col justify-between">
                <div>
                  <CardHeader className="flex flex-row items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">
                        {goal.goal_type.replace(/_/g, " ")}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-1.5 mt-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        Target Horizon: <strong className="text-slate-200">{goal.target_years} {goal.target_years === 1 ? "Year" : "Years"}</strong>
                      </CardDescription>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge
                        variant={goal.priority === "HIGH" ? "rose" : goal.priority === "MEDIUM" ? "amber" : "slate"}
                        size="sm"
                      >
                        {goal.priority} Priority
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="flex items-baseline justify-between">
                      <div>
                        <span className="text-xs text-slate-400">Current Accumulated</span>
                        <p className="text-lg font-bold text-emerald-400">{formatINR(goal.current_amount)}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-400">Target Corpus</span>
                        <p className="text-lg font-bold text-slate-100">{formatINR(goal.target_amount)}</p>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs text-slate-300">
                        <span>Funding Progress</span>
                        <span className="font-semibold">{progressPct}%</span>
                      </div>
                      <Progress
                        value={progressPct}
                        indicatorColor={progressPct >= 75 ? "emerald" : progressPct >= 40 ? "blue" : "amber"}
                      />
                    </div>

                    {feasibility && (
                      <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Required Monthly SIP:</span>
                          <span className="font-semibold text-sky-400">{formatINR(feasibility.required_monthly_sip)}/mo</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Projected Corpus:</span>
                          <span className="font-semibold text-emerald-300">{formatINR(feasibility.projected_corpus)}</span>
                        </div>
                        <p className="text-[11px] text-slate-300 pt-1 border-t border-slate-700/40">
                          {feasibility.recommendation}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </div>

                <CardFooter className="flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Compounding Annuity Formula
                  </span>
                  <Badge variant={progressPct >= 70 ? "emerald" : "blue"} size="sm">
                    {progressPct >= 70 ? "On Track" : "Accumulating"}
                  </Badge>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Goal Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
          <Card className="max-w-md w-full border-slate-700 shadow-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Add New Financial Goal</CardTitle>
                <CardDescription>Specify target amount and timeline in INR</CardDescription>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-100 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </CardHeader>

            <form onSubmit={handleCreateGoal}>
              <CardContent className="space-y-4">
                <Select
                  label="Goal Category"
                  value={newGoal.goal_type}
                  onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value as GoalType })}
                  options={[
                    { value: "EMERGENCY_FUND", label: "Emergency Fund Buffer" },
                    { value: "HOUSE_DOWNPAYMENT", label: "House Downpayment" },
                    { value: "RETIREMENT", label: "Retirement Corpus" },
                    { value: "EDUCATION", label: "Higher Education" },
                    { value: "WEALTH_CREATION", label: "Long-Term Wealth Creation" },
                    { value: "OTHER", label: "Custom Life Goal" },
                  ]}
                />

                <Input
                  label="Target Corpus Amount (INR)"
                  type="number"
                  prefixSymbol="₹"
                  min={10000}
                  step={25000}
                  value={newGoal.target_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, target_amount: parseFloat(e.target.value) || 0 })}
                  required
                />

                <Input
                  label="Current Already Accumulated (INR)"
                  type="number"
                  prefixSymbol="₹"
                  min={0}
                  step={10000}
                  value={newGoal.current_amount}
                  onChange={(e) => setNewGoal({ ...newGoal, current_amount: parseFloat(e.target.value) || 0 })}
                  required
                />

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Target Timeline (Years)"
                    type="number"
                    min={1}
                    max={40}
                    value={newGoal.target_years}
                    onChange={(e) => setNewGoal({ ...newGoal, target_years: parseInt(e.target.value) || 1 })}
                    required
                  />

                  <Select
                    label="Priority"
                    value={newGoal.priority}
                    onChange={(e) => setNewGoal({ ...newGoal, priority: e.target.value as GoalPriority })}
                    options={[
                      { value: "HIGH", label: "High" },
                      { value: "MEDIUM", label: "Medium" },
                      { value: "LOW", label: "Low" },
                    ]}
                  />
                </div>
              </CardContent>

              <CardFooter className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={isSubmitting} className="gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Save & Recalculate
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}
    </main>
  );
}
