const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function refreshAccessToken() {
  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body?.detail ?? "Session refresh failed");
}

function normaliseDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e.msg ?? e.message ?? JSON.stringify(e)).join(", ");
  return JSON.stringify(detail);
}

async function request(path, options = {}) {
  let headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const run = (hdrs) =>
    fetch(`${BASE_URL}${path}`, { credentials: "include", ...options, headers: hdrs });

  let res = await run(headers);
  let body = await res.json().catch(() => ({}));

  // Reactive refresh on 401
  if (res.status === 401 && !path.startsWith("/auth/")) {
    try {
      await refreshAccessToken();
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
    }
  },

  loginUrl: () => `${BASE_URL}/auth/google`,

  loginUser: async (credentials) => {
    return request("/auth/login", { method: "POST", body: JSON.stringify(credentials) });
  },

  registerUser: async (credentials) => {
    return request("/auth/register", { method: "POST", body: JSON.stringify(credentials) });
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
    request("/auth/change-password", { method: "POST", body: JSON.stringify({ old_password: current_password, new_password }) }),

  // ── Billing ────────────────────────────────────────────
  getBillingInfo: () => request("/billing/info"),

  getTransactions: () => request("/billing/transactions"),

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
