"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { UserProfile, FinancialGoal, FinancialAnalysisResponse } from "@/types";
import { profileService, goalsService, analysisService } from "@/services";
import { MOCK_USER_PROFILE, MOCK_GOALS, MOCK_ANALYSIS } from "@/lib/mockData";
import { useToast } from "./useToast";

interface FinancialDataContextType {
  profile: UserProfile;
  goals: FinancialGoal[];
  analysis: FinancialAnalysisResponse;
  isLoading: boolean;
  isBackendConnected: boolean;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  addGoal: (goal: Omit<FinancialGoal, "id" | "created_at" | "updated_at">) => Promise<void>;
  refreshAll: () => Promise<void>;
}

const FinancialDataContext = createContext<FinancialDataContextType | undefined>(undefined);

export function FinancialDataProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<UserProfile>(MOCK_USER_PROFILE);
  const [goals, setGoals] = useState<FinancialGoal[]>(MOCK_GOALS);
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse>(MOCK_ANALYSIS);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const { toast } = useToast();

  const refreshAll = useCallback(async () => {
    setIsLoading(true);
    try {
      const [fetchedProfile, fetchedGoals, fetchedAnalysis] = await Promise.all([
        profileService.getProfile(1),
        goalsService.getGoals(1),
        analysisService.getUserAnalysis(1),
      ]);

      setProfile(fetchedProfile);
      setGoals(fetchedGoals);
      setAnalysis(fetchedAnalysis);
      setIsBackendConnected(true);
    } catch (err: any) {
      console.warn("Backend not available, active fallback enabled:", err.message);
      setIsBackendConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const updateProfile = async (data: Partial<UserProfile>) => {
    const updated = { ...profile, ...data };
    setProfile(updated);

    // Re-run simulation locally or via API
    try {
      const simulated = await analysisService.simulateAnalysis({
        profile: {
          age: updated.age,
          monthly_income: updated.monthly_income,
          monthly_expenses: updated.monthly_expenses,
          total_savings: updated.total_savings,
          monthly_investment_capacity: updated.monthly_investment_capacity,
          total_debt: updated.total_debt,
          risk_tolerance: updated.risk_tolerance,
          investment_experience: updated.investment_experience,
        },
        goals: goals.map((g) => ({
          goal_type: g.goal_type,
          target_amount: g.target_amount,
          current_amount: g.current_amount,
          target_years: g.target_years,
          priority: g.priority,
        })),
      });
      setAnalysis(simulated);
      toast({
        type: "success",
        title: "Profile Updated",
        description: "Your risk score, health metrics, and asset allocation have been recalculated.",
      });
    } catch (err: any) {
      toast({
        type: "info",
        title: "Profile Saved Locally",
        description: "Metrics adjusted based on current parameters.",
      });
    }
  };

  const addGoal = async (newGoalData: Omit<FinancialGoal, "id" | "created_at" | "updated_at">) => {
    const newGoal: FinancialGoal = {
      ...newGoalData,
      id: goals.length + 1,
      user_id: 1,
      created_at: new Date().toISOString(),
    };
    const updatedGoals = [...goals, newGoal];
    setGoals(updatedGoals);

    // Recalculate analysis
    try {
      const simulated = await analysisService.simulateAnalysis({
        profile: {
          age: profile.age,
          monthly_income: profile.monthly_income,
          monthly_expenses: profile.monthly_expenses,
          total_savings: profile.total_savings,
          monthly_investment_capacity: profile.monthly_investment_capacity,
          total_debt: profile.total_debt,
          risk_tolerance: profile.risk_tolerance,
          investment_experience: profile.investment_experience,
        },
        goals: updatedGoals.map((g) => ({
          goal_type: g.goal_type,
          target_amount: g.target_amount,
          current_amount: g.current_amount,
          target_years: g.target_years,
          priority: g.priority,
        })),
      });
      setAnalysis(simulated);
      toast({
        type: "success",
        title: "New Goal Added",
        description: `${newGoal.goal_type.replace(/_/g, " ")} goal has been incorporated into your roadmap.`,
      });
    } catch {
      toast({
        type: "success",
        title: "Goal Added",
        description: "Your goal has been added to the tracking dashboard.",
      });
    }
  };

  return (
    <FinancialDataContext.Provider
      value={{
        profile,
        goals,
        analysis,
        isLoading,
        isBackendConnected,
        updateProfile,
        addGoal,
        refreshAll,
      }}
    >
      {children}
    </FinancialDataContext.Provider>
  );
}

export function useFinancialData() {
  const context = useContext(FinancialDataContext);
  if (!context) {
    throw new Error("useFinancialData must be used within a FinancialDataProvider");
  }
  return context;
}
