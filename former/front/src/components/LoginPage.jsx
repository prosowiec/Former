import { useState } from "react";
import { api } from "../api/client";

export default function LoginPage({ onLogin, onGoogleLogin }) {
  const [mode, setMode] = useState("login");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Shared
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Register only
  const [name, setName] = useState("");
  const [surname, setSurname] = useState("");

  const isRegister = mode === "register";

  function switchMode(next) {
    setMode(next);
    setError(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegister) {
        await api.registerUser({ email, password, name, surname });
        await api.loginUser({ email, password });
      } else {
        await api.loginUser({ email, password });
      }
      await onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleGoogle() {
    onGoogleLogin?.();
    window.location.href = api.loginUrl();
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="logo">former</span>
        <p className="login-desc">
          {isRegister
            ? "Create an account."
            : "Sign in to trigger Airflow DAG runs."}
        </p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </div>

          {isRegister && (
            <div className="login-fields">
              <div className="field">
                <label htmlFor="name">First name</label>
                <input
                  id="name"
                  type="text"
                  placeholder="Jane"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="given-name"
                />
              </div>
              <div className="field">
                <label htmlFor="surname">Last name</label>
                <input
                  id="surname"
                  type="text"
                  placeholder="Smith"
                  value={surname}
                  onChange={(e) => setSurname(e.target.value)}
                  autoComplete="family-name"
                />
              </div>
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
            type="submit"
            disabled={loading}
          >
            {loading
              ? <span className="spinner" />
              : isRegister
              ? "Create account"
              : "Sign in"}
          </button>
        </form>

        <div className="login-divider">
          <span>or</span>
        </div>

        <button className="login-btn" onClick={handleGoogle} type="button">
          <GoogleIcon />
          Continue with Google
        </button>

        <p className="login-toggle">
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            type="button"
            className="advanced-toggle"
            onClick={() => switchMode(isRegister ? "login" : "register")}
          >
            {isRegister ? "Sign in" : "Register"}
          </button>
        </p>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z"
        fill="#EA4335"
      />
    </svg>
  );
}