import { apiClient } from "./api";
import { FinancialGoal } from "@/types";
import { MOCK_GOALS } from "@/lib/mockData";

export const goalsService = {
  async getGoals(userId: number = 1): Promise<FinancialGoal[]> {
    try {
      const goals = await apiClient<FinancialGoal[]>(`/goals/${userId}`);
      if (goals && goals.length > 0) {
        return goals;
      }
      return MOCK_GOALS;
    } catch (err: any) {
      console.warn("Using default goals (backend returned error or offline):", err.message);
      return MOCK_GOALS;
    }
  },

  async createGoal(goalData: Omit<FinancialGoal, "id" | "created_at" | "updated_at">): Promise<FinancialGoal> {
    return await apiClient<FinancialGoal>("/goals", {
      method: "POST",
      body: JSON.stringify(goalData),
    });
  },
};
