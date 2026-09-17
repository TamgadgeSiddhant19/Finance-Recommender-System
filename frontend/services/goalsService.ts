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

  async updateGoal(
    goalId: number,
    goalData: Partial<FinancialGoal>
  ): Promise<FinancialGoal> {
    return await apiClient<FinancialGoal>(`/goals/${goalId}`, {
      method: "PUT",
      body: JSON.stringify(goalData),
    });
  },

  async deleteGoal(goalId: number): Promise<void> {
    await apiClient<void>(`/goals/${goalId}`, {
      method: "DELETE",
    });
  },

  async getGoalProjection(
    goalId: number,
    overrides?: {
      expected_annual_return?: number;
      inflation_rate?: number;
      monthly_contribution?: number;
    }
  ): Promise<import("@/types").GoalProjectionResponse> {
    return await apiClient<import("@/types").GoalProjectionResponse>(
      `/goals/${goalId}/projection`,
      {
        method: "POST",
        body: JSON.stringify(overrides || {}),
      }
    );
  },

  async simulateGoalProjection(
    payload: {
      goal_type?: string;
      target_amount: number;
      current_amount?: number;
      target_years: number;
      monthly_contribution?: number;
      expected_annual_return?: number;
      inflation_rate?: number;
      priority?: string;
    }
  ): Promise<import("@/types").GoalProjectionResponse> {
    return await apiClient<import("@/types").GoalProjectionResponse>(
      "/goals/projection/simulate",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },
};

