const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });

  const body = await res.json().catch(() => ({}));

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
  logout: () => request("/auth/logout", { method: "POST" }),
  loginUrl: () => `${BASE_URL}/auth/google`,
  loginUser: (credentials) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),
  registerUser: (credentials) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  // DAG
  trigger: (payload) =>
    request("/airflow/trigger", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};