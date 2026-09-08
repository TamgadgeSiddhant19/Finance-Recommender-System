import { apiClient, tokenStorage } from "./api";
import { AuthTokenResponse, AuthUser, LoginPayload, RegisterPayload } from "@/types";

export const authService = {
  /**
   * Registers a new user and returns JWT session
   */
  async register(data: RegisterPayload): Promise<AuthTokenResponse> {
    const res = await apiClient<AuthTokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      tokenStorage.set(res.access_token);
    }
    return res;
  },

  /**
   * Logs in a user and stores JWT access token
   */
  async login(data: LoginPayload): Promise<AuthTokenResponse> {
    const res = await apiClient<AuthTokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      tokenStorage.set(res.access_token);
    }
    return res;
  },

  /**
   * Fetches currently authenticated user
   */
  async getCurrentUser(): Promise<AuthUser> {
    return await apiClient<AuthUser>("/auth/me");
  },

  /**
   * Logs out user session locally and notifies backend
   */
  async logout(): Promise<void> {
    try {
      await apiClient("/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    } finally {
      tokenStorage.clear();
    }
  },
};
