import { useState } from "react";
import { api } from "../api/client";

export default function ChangeEmailModal({ currentEmail, onClose, onSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.changeEmail(email, password);
      setDone(true);
    } catch (err) {
      setError(err.message ?? "Failed to change email.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={{ maxWidth: 420 }} onClick={(event) => event.stopPropagation()}>
        <div className="modal__header">
          <span className="modal__title">Change email</span>
          <button className="modal__close" onClick={onClose} aria-label="Close"><CloseIcon /></button>
        </div>
        <div className="modal__body">
          {done ? (
            <div className="profile-change-success">
              <span className="profile-change-success__icon">✓</span>
              <p>A verification link was sent to <strong>{email}</strong>.</p>
              <span>Verify the address, then sign in with your new email.</span>
              <button className="submit-btn submit-btn--full" onClick={onSuccess}>Continue to sign in</button>
            </div>
          ) : (
            <form className="login-form" onSubmit={handleSubmit} noValidate>
              <p className="profile-change-note">Current email: <strong>{currentEmail}</strong></p>
              <div className="field">
                <label htmlFor="change-email-new">New email</label>
                <input
                  id="change-email-new"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                  autoFocus
                />
              </div>
              <div className="field">
                <label htmlFor="change-email-password">Current password</label>
                <input
                  id="change-email-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
                <span className="field__hint">Required to protect changes to your sign-in address.</span>
              </div>
              {error && <div className="banner banner--error"><span className="banner__label">Error</span><span>{error}</span></div>}
              <div className="profile-change-actions">
                <button type="button" className="logout-btn" onClick={onClose}>Cancel</button>
                <button type="submit" className="submit-btn" disabled={loading || !email || !password}>
                  {loading ? <span className="spinner" /> : "Change email"}
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
