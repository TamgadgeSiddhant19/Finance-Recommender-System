import { apiClient } from "./api";
import { FinancialGoal } from "@/types";

export const goalsService = {
  async getMyGoals(): Promise<FinancialGoal[]> {
    try {
      const goals = await apiClient<FinancialGoal[]>("/goals/me");
      if (Array.isArray(goals)) {
        return goals;
      }
      return [];
    } catch (err: any) {
      return [];
    }
  },

  async getGoals(userId: number = 1): Promise<FinancialGoal[]> {
    try {
      const goals = await apiClient<FinancialGoal[]>(`/goals/${userId}`);
      if (Array.isArray(goals)) {
        return goals;
      }
      return [];
    } catch (err: any) {
      return [];
    }
  },

  async createGoal(goalData: Omit<FinancialGoal, "id" | "created_at" | "updated_at">): Promise<FinancialGoal> {
    return await apiClient<FinancialGoal>("/goals", {
      method: "POST",
      body: JSON.stringify(goalData),
    });
  },
};
