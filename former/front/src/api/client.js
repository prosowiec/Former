const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = body?.detail ?? `HTTP ${res.status}`;
    throw new Error(message);
  }

  return body;
}

export const api = {
  health: () => request("/health"),
  trigger: (payload) =>
    request("/airflow/trigger", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};