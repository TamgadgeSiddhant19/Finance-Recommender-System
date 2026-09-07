import { apiClient } from "./api";
import { UserProfile } from "@/types";
import { MOCK_USER_PROFILE } from "@/lib/mockData";

export const profileService = {
  async getProfile(userId: number = 1): Promise<UserProfile> {
    try {
      return await apiClient<UserProfile>(`/profile/${userId}`);
    } catch (err: any) {
      // Return realistic mock profile if user has not yet registered in local DB
      console.warn("Using default financial profile (backend returned 404 or offline):", err.message);
      return MOCK_USER_PROFILE;
    }
  },

  async createProfile(profileData: Omit<UserProfile, "id" | "created_at" | "updated_at">): Promise<UserProfile> {
    return await apiClient<UserProfile>("/profile", {
      method: "POST",
      body: JSON.stringify(profileData),
    });
  },

  async updateProfile(userId: number, profileData: Partial<UserProfile>): Promise<UserProfile> {
    return await apiClient<UserProfile>(`/profile/${userId}`, {
      method: "PUT",
      body: JSON.stringify(profileData),
    });
  },
};
