import { apiClient } from "./api";
import { UserProfile } from "@/types";

export const profileService = {
  async getMyProfile(): Promise<UserProfile | null> {
    try {
      return await apiClient<UserProfile>("/profile/me");
    } catch (err: any) {
      return null;
    }
  },

  async getProfile(userId: number = 1): Promise<UserProfile | null> {
    try {
      return await apiClient<UserProfile>(`/profile/${userId}`);
    } catch (err: any) {
      return null;
    }
  },

  async createProfile(profileData: Omit<UserProfile, "id" | "created_at" | "updated_at">): Promise<UserProfile> {
    return await apiClient<UserProfile>("/profile", {
      method: "POST",
      body: JSON.stringify(profileData),
    });
  },

  async updateMyProfile(profileData: Partial<UserProfile>): Promise<UserProfile> {
    return await apiClient<UserProfile>("/profile/me", {
      method: "PUT",
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
