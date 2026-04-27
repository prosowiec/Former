const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

// Token management
let accessToken = localStorage.getItem("access_token");
let refreshToken = localStorage.getItem("refresh_token");

export function setTokens(access_token, refresh_token) {
  accessToken = access_token;
  refreshToken = refresh_token;
  if (access_token) localStorage.setItem("access_token", access_token);
  if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
}

export function getAccessToken() {
  return accessToken;
}

export function clearTokens() {
  console.log("Clearing tokens...");
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  console.log("Tokens cleared. access_token in localStorage:", localStorage.getItem("access_token"));
}

async function refreshAccessToken() {
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }

  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const body = await res.json().catch(() => ({}));

    if (!res.ok) {
      clearTokens();
      throw new Error(body?.detail ?? "Token refresh failed");
    }

    setTokens(body.access_token, body.refresh_token);
    return body.access_token;
  } catch (error) {
    clearTokens();
    throw error;
  }
}

async function request(path, options = {}) {
  let headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add Bearer token if available
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    headers,
    credentials: "include",
    ...options,
  });

  const body = await res.json().catch(() => ({}));

  // Handle token expiration - try to refresh and retry
  if (res.status === 401 && refreshToken && path !== "/auth/refresh") {
    try {
      const newAccessToken = await refreshAccessToken();
      headers["Authorization"] = `Bearer ${newAccessToken}`;
      
      // Retry the request with new token
      const retryRes = await fetch(`${BASE_URL}${path}`, {
        headers,
        credentials: "include",
        ...options,
      });

      const retryBody = await retryRes.json().catch(() => ({}));

      if (!retryRes.ok) {
        let message = retryBody?.detail ?? `HTTP ${retryRes.status}`;
        if (typeof message === "object") {
          if (Array.isArray(message)) {
            message = message.map(err => err.msg || err.message || JSON.stringify(err)).join(", ");
          } else {
            message = JSON.stringify(message);
          }
        }
        throw new Error(message);
      }

      return retryBody;
    } catch (refreshError) {
      // If refresh fails, user needs to login again
      throw new Error("Session expired. Please login again.");
    }
  }

  if (!res.ok) {
    let message = body?.detail ?? `HTTP ${res.status}`;
    
    // Handle validation errors (array of objects) or other object responses
    if (typeof message === 'object') {
      if (Array.isArray(message)) {
        message = message.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
      } else {
        message = JSON.stringify(message);
      }
    }
    
    throw new Error(message);
  }

  return body;
}

export const api = {
  health: () => request("/health"),

  // Auth
  me: () => request("/auth/me"),
  logout: async () => {
    console.log("Logging out...");
    // Simple fetch without the complex request wrapper to avoid token refresh logic
    try {
      await fetch(`${BASE_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
    } catch (e) {
      console.log("Logout API call failed:", e.message);
    } finally {
      clearTokens();
      console.log("Logout complete");
    }
  },
  loginUrl: () => `${BASE_URL}/auth/google`,
  loginUser: async (credentials) => {
    const response = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    if (response.tokens) {
      setTokens(response.tokens.access_token, response.tokens.refresh_token);
    }
    return response;
  },
  registerUser: async (credentials) => {
    const response = await request("/auth/register", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    if (response.tokens) {
      setTokens(response.tokens.access_token, response.tokens.refresh_token);
    }
    return response;
  },
  // DAG
  trigger: (payload) =>
    request("/airflow/trigger", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

    getRuns: () => Promise.resolve([]),
};