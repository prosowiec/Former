import { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { useRuns } from "./hooks/useRuns";
import LandingPage from "./components/LandingPage";
import LoginPage from "./components/LoginPage";
import OAuthSuccess from "./components/OAuthSuccess";
import HealthBadge from "./components/HealthBadge";
import StatsBar from "./components/StatsBar";
import TriggerForm from "./components/TriggerForm";
import RunsTable from "./components/RunsTable";
import "./index.css";

export default function App() {
  const navigate = useNavigate();
  const { user, loading: authLoading, logout, login, refetchUser } = useAuth();
  const { runs, loading: runsLoading, addRun, stats } = useRuns();
  const [successBanner, setSuccessBanner] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  if (authLoading) {
    return (
      <div className="loading-screen">
        <span className="spinner spinner--dark" />
      </div>
    );
  }

  function handleTriggerSuccess(result, runName) {
    const newRun = {
      dag_run_id: result.dag_run_id,
      form_url: result.airflow_response?.conf?.form_url ?? "—",
      run_name: runName,
      state: result.state,
      dag_id: result.dag_id,
      num_executions: result.num_executions,
      base_interval_minutes: result.base_interval_minutes,
      interval_jitter_minutes: result.interval_jitter_minutes,
      created_at: new Date().toISOString(),
    };
    addRun(newRun);
    setSuccessBanner(`"${runName}" triggered successfully`);
    setTimeout(() => setSuccessBanner(null), 4000);
  }

  const TABS = [
    { id: "all", label: "All" },
    { id: "running", label: "Running" },
    { id: "done", label: "Done" },
    { id: "failed", label: "Failed" },
  ];

  const filteredRuns = runs.filter((r) => {
    if (activeTab === "running") return r.state === "running" || r.state === "queued";
    if (activeTab === "done") return r.state === "success";
    if (activeTab === "failed") return r.state === "failed";
    return true;
  });

  const dashboardElement = user ? (
    <div className="app">
      <header className="header">
        <button className="logo logo--btn" onClick={() => navigate("/landing")}>
          former
        </button>
        <div className="header-right">
          <HealthBadge />
          <div className="user-menu">
            {user.picture && (
              <img
                className="avatar"
                src={user.picture}
                alt={user.name}
                referrerPolicy="no-referrer"
              />
            )}
            <span className="user-name">{user.name ?? user.email}</span>
            <button
              className="logout-btn"
              onClick={async () => {
                await logout();
                navigate("/landing");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="main main--wide">
        <div className="dashboard-hero">
          <div className="dashboard-hero__text">
            <h1>Form filler</h1>
            <p>
              Submit a university form URL and let the LLM pipeline handle the rest —
              fetching, filling, and submitting automatically.
            </p>
          </div>
          <StatsBar stats={stats} />
        </div>

        <div className="card">
          <div className="card__header">
            <span className="card__title">New run</span>
          </div>
          {successBanner && (
            <div className="banner banner--success">
              <span className="banner__label">Triggered</span>
              <span>{successBanner}</span>
            </div>
          )}
          <TriggerForm onSuccess={handleTriggerSuccess} />
        </div>

        <div className="card">
          <div className="card__header">
            <span className="card__title">Runs</span>
            <div className="tabs">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  className={`tab${activeTab === t.id ? " tab--active" : ""}`}
                  onClick={() => setActiveTab(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          <RunsTable runs={filteredRuns} loading={runsLoading} />
        </div>
      </main>
    </div>
  ) : null;

  return (
    <Routes>
      <Route
        path="/"
        element={user ? <Navigate to="/home" replace /> : <Navigate to="/landing" replace />}
      />
      <Route
        path="/landing"
        element={user ? <Navigate to="/home" replace /> : <LandingPage onGoToApp={() => navigate("/login")} />}
      />
      <Route
        path="/login"
        element={user ? <Navigate to="/home" replace /> : (
          <LoginPage
            onLogin={async () => {
              await refetchUser();
              navigate("/home");
            }}
            onGoogleLogin={login}
            onBack={() => navigate("/landing")}
          />
        )}
      />
      <Route path="/oauth-success" element={<OAuthSuccess />} />
      <Route path="/home" element={dashboardElement || <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to={user ? "/home" : "/landing"} replace />} />
    </Routes>
  );
}
