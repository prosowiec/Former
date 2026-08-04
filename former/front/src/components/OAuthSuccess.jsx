import { useEffect } from "react";
import { setTokens } from "../api/client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export default function OAuthSuccess() {
  useEffect(() => {
    fetch(`${BASE_URL}/auth/tokens`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data) => {
        if (!data.access_token || !data.refresh_token) {
          throw new Error("Tokens missing from response");
        }
        setTokens(data.access_token, data.refresh_token);
        // Go straight to the protected route. PrivateRoute waits for /auth/me
        // to resolve, so the user cannot be redirected to the landing page
        // during the post-OAuth authentication race.
        window.location.replace("/home");
      })
      .catch((err) => {
        console.error("OAuth failed:", err);
        window.location.replace("/login");
      });
  }, []);

  return (
    <div className="loading-screen">
      <span className="spinner spinner--dark" />
    </div>
  );
}
