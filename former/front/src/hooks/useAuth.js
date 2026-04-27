import { useEffect, useState, useCallback } from "react";
import { api, setTokens, clearTokens, getAccessToken } from "../api/client";

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
  if (window.location.pathname === "/oauth-success") {
    fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/tokens`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        if (!data.access_token) throw new Error("No tokens");

        setTokens(data.access_token, data.refresh_token);

        window.history.replaceState({}, document.title, "/");

        refetchUser(); // or setUser(...)
      })
      .catch(err => console.error("OAuth failed:", err));
  }
}, []);

  useEffect(() => {
    // Restore tokens from localStorage on component mount
    const accessToken = localStorage.getItem("access_token");
    const refreshToken = localStorage.getItem("refresh_token");
    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
    }

    fetchMe();

    // If we're returning from Google OAuth, strip the query param then recheck
    const params = new URLSearchParams(window.location.search);
    if (params.get("login") === "success") {
      window.history.replaceState({}, "", window.location.pathname);
      fetchMe(); // Fetch updated user info after Google auth redirect
    }
  }, [fetchMe]);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    window.location.href = "/";
  }, []);

  const login = useCallback(() => {
    window.location.href = api.loginUrl();
  }, []);

  const loginLocal = useCallback(
    async (email, password) => {
      await api.loginUser({ email, password });
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