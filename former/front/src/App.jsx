import { useState } from "react";
import { useAuth } from "./hooks/useAuth";
import TriggerForm from "./components/TriggerForm";
import RunResult from "./components/RunResult";
import HealthBadge from "./components/HealthBadge";
import LoginPage from "./components/LoginPage";
import "./index.css";

export default function App() {
  const { user, loading, logout, login, refetchUser } = useAuth();
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (loading) {
    return (
      <div className="loading-screen">
        <span className="spinner spinner--dark" />
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={refetchUser} onGoogleLogin={login} />;
  }

  return (
    <div className="app">
      <header className="header">
        <span className="logo">former</span>
        <div className="header-right">
          <HealthBadge />
          <div className="user-menu">
            {user.picture && (
              <img className="avatar" src={user.picture} alt={user.name} referrerPolicy="no-referrer" />
            )}
            <span className="user-name">{user.name ?? user.email}</span>
            <button className="logout-btn" onClick={logout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="page-title">
          <h1>Trigger a DAG run</h1>
          <p>Submit a form URL to kick off the Airflow pipeline.</p>
        </div>

        <TriggerForm setResult={setResult} setError={setError} />

        {error && (
          <div className="banner banner--error">
            <span className="banner__label">Error</span>
            <span>{error}</span>
          </div>
        )}

        {result && <RunResult result={result} />}
      </main>
    </div>
  );
}