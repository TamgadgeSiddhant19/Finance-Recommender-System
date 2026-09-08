"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { UserProfile, FinancialGoal, FinancialAnalysisResponse } from "@/types";
import { profileService, goalsService, analysisService } from "@/services";
import { useToast } from "./useToast";
import { useAuth } from "./useAuth";

interface FinancialDataContextType {
  profile: UserProfile | null;
  goals: FinancialGoal[];
  analysis: FinancialAnalysisResponse | null;
  hasProfile: boolean;
  hasGoals: boolean;
  isLoading: boolean;
  isBackendConnected: boolean;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  addGoal: (goal: Omit<FinancialGoal, "id" | "created_at" | "updated_at">) => Promise<void>;
  refreshAll: () => Promise<void>;
}

const FinancialDataContext = createContext<FinancialDataContextType | undefined>(undefined);

export function FinancialDataProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(true);
  const { toast } = useToast();

  const refreshAll = useCallback(async () => {
    if (isAuthLoading) return;

    if (!isAuthenticated) {
      setProfile(null);
      setGoals([]);
      setAnalysis(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      // Authenticated user: fetch user's live Neon DB data via /profile/me, /goals/me, /analysis/me
      const [fetchedProfile, fetchedGoals, fetchedAnalysis] = await Promise.all([
        profileService.getMyProfile(),
        goalsService.getMyGoals(),
        analysisService.getMyAnalysis(),
      ]);

      setProfile(fetchedProfile);
      setGoals(fetchedGoals || []);
      setAnalysis(fetchedAnalysis);
      setIsBackendConnected(true);
    } catch (err: any) {
      console.warn("Failed to fetch live financial data:", err.message);
      setIsBackendConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, isAuthLoading]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const updateProfile = async (data: Partial<UserProfile>) => {
    if (!isAuthenticated) {
      toast({
        type: "error",
        title: "Authentication Required",
        description: "Please sign in to update your financial profile.",
      });
      return;
    }

    try {
      let savedProfile: UserProfile;
      if (profile && profile.id) {
        savedProfile = await profileService.updateMyProfile(data);
      } else {
        savedProfile = await profileService.createProfile({
          age: Number(data.age ?? 30),
          monthly_income: Number(data.monthly_income ?? 100000),
          monthly_expenses: Number(data.monthly_expenses ?? 50000),
          total_savings: Number(data.total_savings ?? 200000),
          monthly_investment_capacity: Number(data.monthly_investment_capacity ?? (Number(data.monthly_income ?? 100000) - Number(data.monthly_expenses ?? 50000))),
          total_debt: Number(data.total_debt ?? 0),
          risk_tolerance: data.risk_tolerance ?? "MODERATE",
          investment_experience: data.investment_experience ?? "INTERMEDIATE",
        });
      }
      setProfile(savedProfile);

      // Re-fetch analysis
      const updatedAnalysis = await analysisService.getMyAnalysis();
      setAnalysis(updatedAnalysis);

      toast({
        type: "success",
        title: "Profile Updated",
        description: "Your financial profile has been saved to your account and metrics recalculated.",
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: "Update Failed",
        description: err.message || "Failed to save financial profile.",
      });
    }
  };

  const addGoal = async (newGoalData: Omit<FinancialGoal, "id" | "created_at" | "updated_at">) => {
    if (!isAuthenticated || !user) {
      toast({
        type: "error",
        title: "Authentication Required",
        description: "Please sign in to add financial goals.",
      });
      return;
    }

    try {
      const savedGoal = await goalsService.createGoal({
        ...newGoalData,
        user_id: user.id,
      });

      const updatedGoals = [...goals, savedGoal];
      setGoals(updatedGoals);

      // Re-fetch analysis with new goal
      const updatedAnalysis = await analysisService.getMyAnalysis();
      setAnalysis(updatedAnalysis);

      toast({
        type: "success",
        title: "New Goal Added",
        description: `${savedGoal.goal_type.replace(/_/g, " ")} goal has been incorporated into your roadmap.`,
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: "Goal Creation Failed",
        description: err.message || "Unable to save goal to database.",
      });
    }
  };

  return (
    <FinancialDataContext.Provider
      value={{
        profile,
        goals,
        analysis,
        hasProfile: profile !== null,
        hasGoals: goals.length > 0,
        isLoading: isLoading || isAuthLoading,
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
