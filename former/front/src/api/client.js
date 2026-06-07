const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

let accessToken = sessionStorage.getItem("access_token");
let refreshToken = sessionStorage.getItem("refresh_token");

function decodeToken(token) {
  if (!token) return null;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (e) {
    console.error("Failed to decode token:", e);
    return null;
  }
}

function isTokenExpired(token) {
  const decoded = decodeToken(token);
  if (!decoded || !decoded.exp) return true;
  const expirationTime = decoded.exp * 1000;
  const now = Date.now();
  const bufferMs = 60 * 1000;
  return now >= expirationTime - bufferMs;
}

export function setTokens(access_token, refresh_token) {
  accessToken = access_token;
  refreshToken = refresh_token;
  if (access_token) sessionStorage.setItem("access_token", access_token);
  if (refresh_token) sessionStorage.setItem("refresh_token", refresh_token);
}

export function getAccessToken() {
  return accessToken;
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}

async function refreshAccessToken() {
  if (!refreshToken) throw new Error("No refresh token available");
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

function normaliseDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e.msg ?? e.message ?? JSON.stringify(e)).join(", ");
  return JSON.stringify(detail);
}

async function request(path, options = {}) {
  // Proactive refresh before request if token is expiring
  if (accessToken && isTokenExpired(accessToken) && refreshToken && path !== "/auth/refresh") {
    try {
      accessToken = await refreshAccessToken();
    } catch (error) {
      console.error("Proactive token refresh failed:", error);
      throw error;
    }
  }

  let headers = {
    "Content-Type": "application/json",
    ...options.headers,
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };

  const run = (hdrs) =>
    fetch(`${BASE_URL}${path}`, { credentials: "include", ...options, headers: hdrs });

  let res = await run(headers);
  let body = await res.json().catch(() => ({}));

  // Reactive refresh on 401
  if (res.status === 401 && refreshToken && path !== "/auth/refresh") {
    try {
      const newToken = await refreshAccessToken();
      headers = { ...headers, Authorization: `Bearer ${newToken}` };
      res = await run(headers);
      body = await res.json().catch(() => ({}));
    } catch {
      throw new Error("Session expired. Please log in again.");
    }
  }

  if (!res.ok) throw new Error(normaliseDetail(body?.detail ?? `HTTP ${res.status}`));

  return body;
}

export const api = {
  health: () => request("/health"),

  // ── Auth ───────────────────────────────────────────────
  me: () => request("/auth/me"),

  logout: async () => {
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
    }
  },

  loginUrl: () => `${BASE_URL}/auth/google`,

  loginUser: async (credentials) => {
    const res = await request("/auth/login", { method: "POST", body: JSON.stringify(credentials) });
    if (res.tokens) setTokens(res.tokens.access_token, res.tokens.refresh_token);
    return res;
  },

  registerUser: async (credentials) => {
    const res = await request("/auth/register", { method: "POST", body: JSON.stringify(credentials) });
    if (res.tokens) setTokens(res.tokens.access_token, res.tokens.refresh_token);
    return res;
  },

  // ── Email verification & password reset ───────────────
  sendVerificationEmail: (email) =>
    request("/auth/verify-email/send", { method: "POST", body: JSON.stringify({ email }) }),

  verifyEmail: (token) =>
    request("/auth/verify-email", { method: "POST", body: JSON.stringify({ token }) }),

  requestPasswordReset: (email) =>
    request("/auth/password-reset/request", { method: "POST", body: JSON.stringify({ email }) }),

  confirmPasswordReset: (token, new_password) =>
    request("/auth/password-reset/confirm", { method: "POST", body: JSON.stringify({ token, new_password }) }),

  changePassword: (current_password, new_password) =>
    request("/auth/change-password", { method: "POST", body: JSON.stringify({ current_password, new_password }) }),

  // ── Billing ────────────────────────────────────────────
  getBillingInfo: () => request("/billing/info"),

  getTransactions: () => request("/billing/transactions"),

  createTransaction: (payload) =>
    request("/billing/transaction", { method: "POST", body: JSON.stringify(payload) }),

  deductFormFills: (form_fills_to_deduct) =>
    request("/billing/deduct-form-fills", {
      method: "POST",
      body: JSON.stringify({ form_fills_to_deduct }),
    }),

  createPaymentIntent: (payload) =>
    request("/billing/create-payment-intent", { method: "POST", body: JSON.stringify(payload) }),

  confirmPayment: (payload) =>
    request("/billing/confirm-payment", { method: "POST", body: JSON.stringify(payload) }),

  // ── DAG ────────────────────────────────────────────────
  trigger: (payload) =>
    request("/airflow/trigger", { method: "POST", body: JSON.stringify(payload) }),

  getRuns: () => request("/airflow/runs"),

  cancelRun: (dag_run_id) =>
    request(`/airflow/runs/${dag_run_id}/cancel`, { method: "POST" }),
};