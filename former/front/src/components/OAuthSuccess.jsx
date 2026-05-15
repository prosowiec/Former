import { useEffect } from "react";
import { setTokens } from "../api/client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export default function OAuthSuccess() {
  useEffect(() => {
    fetch(`${BASE_URL}/auth/tokens`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.access_token) {
          throw new Error("No tokens received");
        }

        setTokens(data.access_token, data.refresh_token);

        // Redirect with a full reload so the SPA can reinitialize with auth state.
        window.location.replace("/home");
      })
      .catch((err) => {
        console.error("OAuth failed:", err);
        window.location.replace("/login");
      });
  }, []);

  return <div>Logging you in via Google...</div>;
}