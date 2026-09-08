"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { AuthUser, LoginPayload, RegisterPayload } from "@/types";
import { authService, tokenStorage } from "@/services";
import { useToast } from "./useToast";

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { toast } = useToast();

  const refreshUser = useCallback(async () => {
    const token = tokenStorage.get();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err: any) {
      console.warn("Session expired or invalid token:", err.message);
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (credentials: LoginPayload) => {
    setIsLoading(true);
    try {
      const tokenResp = await authService.login(credentials);
      setUser(tokenResp.user);
      toast({
        type: "success",
        title: "Welcome Back!",
        description: `Signed in as ${tokenResp.user.email}.`,
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: "Login Failed",
        description: err.message || "Invalid email or password.",
      });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: RegisterPayload) => {
    setIsLoading(true);
    try {
      const tokenResp = await authService.register(payload);
      setUser(tokenResp.user);
      toast({
        type: "success",
        title: "Account Created!",
        description: "Welcome to ArthaAI! Your financial profile is ready to set up.",
      });
    } catch (err: any) {
      toast({
        type: "error",
        title: "Registration Failed",
        description: err.message || "Could not register account.",
      });
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      toast({
        type: "info",
        title: "Logged Out",
        description: "You have been successfully signed out.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
