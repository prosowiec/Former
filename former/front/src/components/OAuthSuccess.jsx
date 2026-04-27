import { useEffect } from "react";
import { setTokens } from "../api/client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export default function OAuthSuccess() {
  useEffect(() => {
    fetch(`${BASE_URL}/auth/tokens`, {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => {
        if (!data.access_token) {
          throw new Error("No tokens received");
        }

        setTokens(data.access_token, data.refresh_token);

        // redirect after login
        window.location.href = "/";
      })
      .catch((err) => {
        console.error("OAuth failed:", err);
        window.location.href = "/login";
      });
  }, []);

  return <div>Logging you in via Google...</div>;
}