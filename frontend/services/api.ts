const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

const TOKEN_STORAGE_KEY = "arthai_auth_token";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export const tokenStorage = {
  get(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  },
  set(token: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  },
  clear() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  },
};

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const token = tokenStorage.get();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorData: any;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }

      // If token expired or unauthorized, clear token
      if (response.status === 401 && token) {
        tokenStorage.clear();
      }

      let errorMessage = `API Request failed with status ${response.status}`;
      if (typeof errorData?.detail === "string") {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData?.detail)) {
        errorMessage = errorData.detail
          .map((e: any) => {
            if (typeof e === "string") return e;
            const field = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : "";
            return field ? `${field}: ${e.msg || JSON.stringify(e)}` : e.msg || JSON.stringify(e);
          })
          .join("; ");
      } else if (errorData?.detail && typeof errorData.detail === "object") {
        errorMessage = JSON.stringify(errorData.detail);
      } else if (errorData?.message) {
        errorMessage = typeof errorData.message === "string" ? errorData.message : JSON.stringify(errorData.message);
      }

      throw new ApiError(
        errorMessage,
        response.status,
        errorData
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or connection error
    throw new ApiError(
      error?.message || "Unable to reach the backend server.",
      0,
      { isNetworkError: true }
    );
  }
}
