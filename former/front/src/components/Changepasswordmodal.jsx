import { useState } from "react";
import { api } from "../api/client";

export default function ChangePasswordModal({ onClose }) {
  const [current,  setCurrent]  = useState("");
  const [next,     setNext]     = useState("");
  const [next2,    setNext2]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [done,     setDone]     = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (next !== next2)   { setError("New passwords do not match."); return; }
    if (next.length < 8)  { setError("Password must be at least 8 characters."); return; }
    setError(null);
    setLoading(true);
    try {
      await api.changePassword(current, next);
      setDone(true);
    } catch (err) {
      setError(err.message ?? "Failed to change password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: 400 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <span className="modal__title">Change password</span>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        <div className="modal__body">
          {done ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, padding: "16px 0", textAlign: "center" }}>
              <span style={{ fontSize: 36 }}>✓</span>
              <p style={{ fontSize: 13, color: "var(--muted)" }}>Password changed successfully.</p>
              <button className="submit-btn submit-btn--full" onClick={onClose}>Done</button>
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit} noValidate>
              <div className="field">
                <label htmlFor="cp-current">Current password</label>
                <input
                  id="cp-current"
                  type="password"
                  placeholder="••••••••"
                  value={current}
                  onChange={(e) => setCurrent(e.target.value)}
                  required
                  autoFocus
                  autoComplete="current-password"
                />
              </div>
              <div className="field">
                <label htmlFor="cp-new">New password</label>
                <input
                  id="cp-new"
                  type="password"
                  placeholder="••••••••"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                  required
                  autoComplete="new-password"
                />
              </div>
              <div className="field">
                <label htmlFor="cp-new2">Confirm new password</label>
                <input
                  id="cp-new2"
                  type="password"
                  placeholder="••••••••"
                  value={next2}
                  onChange={(e) => setNext2(e.target.value)}
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

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 }}>
                <button type="button" className="logout-btn" onClick={onClose}>Cancel</button>
                <button type="submit" className="submit-btn" disabled={loading}>
                  {loading ? <span className="spinner" /> : "Change password"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function CloseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}