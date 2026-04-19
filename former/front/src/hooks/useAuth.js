import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";

export function useAuth() {
  const [user, setUser] = useState(undefined); // undefined = loading
  const [error, setError] = useState(null);

  const fetchMe = useCallback(async () => {
    try {
      const data = await api.me();
      setUser(data.user ?? null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    fetchMe();

    // If we're returning from Google OAuth, strip the query param then recheck
    const params = new URLSearchParams(window.location.search);
    if (params.get("login") === "success") {
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [fetchMe]);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const login = useCallback(() => {
    window.location.href = api.loginUrl();
  }, []);

  const loginLocal = useCallback(
    async (username, password) => {
      await api.loginUser({ username, password });
      await fetchMe();
    },
    [fetchMe]
  );

  return {
    user,
    loading: user === undefined,
    logout,
    login,
    loginLocal,
    refetchUser: fetchMe,
    error,
  };
}