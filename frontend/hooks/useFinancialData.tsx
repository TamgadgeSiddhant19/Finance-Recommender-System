"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { UserProfile, FinancialGoal, FinancialAnalysisResponse, RecommendationResponse } from "@/types";
import { profileService, goalsService, analysisService, recommendationsService } from "@/services";
import { useToast } from "./useToast";
import { useAuth } from "./useAuth";

interface FinancialDataContextType {
  profile: UserProfile | null;
  goals: FinancialGoal[];
  analysis: FinancialAnalysisResponse | null;
  recommendation: RecommendationResponse | null;
  hasProfile: boolean;
  hasGoals: boolean;
  hasRecommendation: boolean;
  isLoading: boolean;
  isBackendConnected: boolean;
  updateProfile: (data: Omit<UserProfile, "id" | "created_at" | "updated_at"> | Partial<UserProfile>) => Promise<UserProfile | null>;
  addGoal: (goal: Omit<FinancialGoal, "id" | "created_at" | "updated_at">) => Promise<void>;
  generateRecommendation: () => Promise<RecommendationResponse | null>;
  refreshAll: () => Promise<void>;
}

const FinancialDataContext = createContext<FinancialDataContextType | undefined>(undefined);

export function FinancialDataProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [analysis, setAnalysis] = useState<FinancialAnalysisResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(true);
  const { toast } = useToast();

  const refreshAll = useCallback(async () => {
    if (isAuthLoading) return;

    if (!isAuthenticated) {
      setProfile(null);
      setGoals([]);
      setAnalysis(null);
      setRecommendation(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      // Authenticated user: fetch user's live Neon DB data via /profile/me, /goals/me, /analysis/me, /recommendations/me/latest
      const [fetchedProfile, fetchedGoals, fetchedAnalysis, fetchedRec] = await Promise.all([
        profileService.getMyProfile(),
        goalsService.getMyGoals(),
        analysisService.getMyAnalysis(),
        recommendationsService.getMyLatestRecommendation(),
      ]);

      setProfile(fetchedProfile);
      setGoals(fetchedGoals || []);
      setAnalysis(fetchedAnalysis);
      setRecommendation(fetchedRec);
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

  const updateProfile = async (data: any): Promise<UserProfile | null> => {
    if (!isAuthenticated) {
      toast({
        type: "error",
        title: "Authentication Required",
        description: "Please sign in to update your financial profile.",
      });
      return null;
    }

    try {
      const payload: Partial<UserProfile> = {
        age: Number(data.age),
        monthly_income: Number(data.monthly_income),
        monthly_expenses: Number(data.monthly_expenses),
        total_savings: Number(data.total_savings),
        monthly_investment_capacity: Number(data.monthly_investment_capacity),
        total_debt: Number(data.total_debt || 0),
        risk_tolerance: (data.risk_tolerance || "MODERATE").toString().toLowerCase() as any,
        investment_experience: (data.investment_experience || "INTERMEDIATE").toString().toLowerCase() as any,
      };

      const savedProfile = await profileService.updateMyProfile(payload);
      setProfile(savedProfile);

      // Re-fetch real backend analysis
      try {
        const updatedAnalysis = await analysisService.getMyAnalysis();
        setAnalysis(updatedAnalysis);
      } catch (analysisErr) {
        console.warn("Could not fetch analysis immediately after saving profile:", analysisErr);
      }

      toast({
        type: "success",
        title: "Profile Saved",
        description: "Your financial profile has been saved to your account and metrics recalculated.",
      });
      return savedProfile;
    } catch (err: any) {
      toast({
        type: "error",
        title: "Save Failed",
        description: err.message || "Failed to save financial profile.",
      });
      throw err;
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

      // Re-fetch real backend analysis
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
      throw err;
    }
  };

  const generateRecommendation = async (): Promise<RecommendationResponse | null> => {
    if (!isAuthenticated) {
      toast({
        type: "error",
        title: "Authentication Required",
        description: "Please sign in to generate portfolio recommendations.",
      });
      return null;
    }

    try {
      const rec = await recommendationsService.generateMyRecommendation();
      setRecommendation(rec);
      toast({
        type: "success",
        title: "Recommendation Generated",
        description: "Your official SEBI-aligned investment roadmap has been generated and saved.",
      });
      return rec;
    } catch (err: any) {
      toast({
        type: "error",
        title: "Generation Failed",
        description: err.message || "Unable to generate recommendation. Please ensure profile and goals are complete.",
      });
      throw err;
    }
  };

  return (
    <FinancialDataContext.Provider
      value={{
        profile,
        goals,
        analysis,
        recommendation,
        hasProfile: profile !== null,
        hasGoals: goals.length > 0,
        hasRecommendation: recommendation !== null,
        isLoading: isLoading || isAuthLoading,
        isBackendConnected,
        updateProfile,
        addGoal,
        generateRecommendation,
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
