import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api } from "../api/client";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const token    = new URLSearchParams(location.search).get("token");

  const [password,  setPassword]  = useState("");
  const [password2, setPassword2] = useState("");
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [done,      setDone]      = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (password !== password2) { setError("Passwords do not match."); return; }
    if (password.length < 8)    { setError("Password must be at least 8 characters."); return; }
    setError(null);
    setLoading(true);
    try {
      await api.confirmPasswordReset(token, password);
      setDone(true);
    } catch (err) {
      setError(err.message ?? "Reset failed. The link may have expired.");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: "center" }}>
          <span className="logo">former</span>
          <p className="login-desc" style={{ color: "var(--red)" }}>Invalid reset link.</p>
          <button className="submit-btn submit-btn--full" onClick={() => navigate("/login")}>Back to sign in</button>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div className="login-page">
        <div className="login-card" style={{ textAlign: "center", gap: "16px" }}>
          <span className="logo">former</span>
          <span style={{ fontSize: 36 }}>✓</span>
          <p className="login-desc">Password reset successfully.</p>
          <button className="submit-btn submit-btn--full" onClick={() => navigate("/login")}>Sign in</button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="logo">former</span>
        <p className="login-desc">Choose a new password.</p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="new-password">New password</label>
            <input
              id="new-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoFocus
              autoComplete="new-password"
            />
          </div>
          <div className="field">
            <label htmlFor="confirm-password">Confirm password</label>
            <input
              id="confirm-password"
              type="password"
              placeholder="••••••••"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>

          {error && (
            <div className="banner banner--error">
              <span className="banner__label">Error</span>
              <span>{error}</span>
            </div>
          )}

          <button className="submit-btn submit-btn--full" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : "Reset password"}
          </button>
        </form>
      </div>
    </div>
  );
}