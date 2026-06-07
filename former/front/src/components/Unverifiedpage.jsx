import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../api/client";

export default function UnverifiedPage() {
  const { user, logout } = useAuth();
  const [sent,    setSent]    = useState(false);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  async function resend() {
    setError(null);
    setLoading(true);
    try {
      await api.sendVerificationEmail(user.email);
      setSent(true);
    } catch (err) {
      setError(err.message ?? "Failed to send email.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card" style={{ textAlign: "center", gap: "16px" }}>
        <span className="logo">former</span>

        <span style={{ fontSize: 36 }}>✉️</span>

        <p style={{ fontWeight: 500, fontSize: 15 }}>Verify your email</p>
        <p className="login-desc">
          We sent a verification link to <strong>{user?.email}</strong>.
          Click it to activate your account.
        </p>

        {sent && (
          <div className="banner banner--success">
            <span className="banner__label">Sent</span>
            <span>Check your inbox.</span>
          </div>
        )}

        {error && (
          <div className="banner banner--error">
            <span className="banner__label">Error</span>
            <span>{error}</span>
          </div>
        )}

        <button
          className="submit-btn submit-btn--full"
          onClick={resend}
          disabled={loading || sent}
        >
          {loading ? <span className="spinner" /> : sent ? "Email sent" : "Resend verification email"}
        </button>

        <button className="advanced-toggle" onClick={logout}>
          Sign out
        </button>
      </div>
    </div>
  );
}