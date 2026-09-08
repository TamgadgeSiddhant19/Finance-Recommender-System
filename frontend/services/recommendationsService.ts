import { apiClient } from "./api";
import {
  RecommendationHistoryItem,
  RecommendationResponse,
  RecommendationSimulateRequest,
} from "@/types/recommendation";

export const recommendationsService = {
  /**
   * Generates and persists a deterministic recommendation for the authenticated user
   */
  async generateMyRecommendation(): Promise<RecommendationResponse> {
    return apiClient<RecommendationResponse>("/recommendations/me", {
      method: "POST",
    });
  },

  /**
   * Retrieves the most recent generated recommendation for the authenticated user
   */
  async getMyLatestRecommendation(): Promise<RecommendationResponse | null> {
    try {
      return await apiClient<RecommendationResponse>("/recommendations/me/latest");
    } catch (err: any) {
      return null;
    }
  },


  /**
   * Generates and persists a deterministic recommendation for a user
   */
  async generateUserRecommendation(userId: number): Promise<RecommendationResponse> {
    return apiClient<RecommendationResponse>(`/recommendations/${userId}`, {
      method: "POST",
    });
  },

  /**
   * Retrieves recommendation history for the authenticated user
   */
  async getMyRecommendationHistory(limit = 10): Promise<RecommendationHistoryItem[]> {
    return apiClient<RecommendationHistoryItem[]>(`/recommendations/me?limit=${limit}`);
  },

  /**
   * Retrieves recommendation history for a user
   */
  async getUserRecommendationHistory(userId: number, limit = 10): Promise<RecommendationHistoryItem[]> {
    return apiClient<RecommendationHistoryItem[]>(`/recommendations/${userId}?limit=${limit}`);
  },

  /**
   * Retrieves a specific saved recommendation by ID
   */
  async getRecommendationById(userId: number, recommendationId: number): Promise<RecommendationResponse> {
    return apiClient<RecommendationResponse>(`/recommendations/${userId}/${recommendationId}`);
  },

  /**
   * Stateless simulation of recommendations
   */
  async simulateRecommendation(data: RecommendationSimulateRequest): Promise<RecommendationResponse> {
    return apiClient<RecommendationResponse>("/recommendations/simulate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};
