import { useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { useRuns } from "./hooks/useRuns";
import LoginPage from "./components/LoginPage";
import HealthBadge from "./components/HealthBadge";
import StatsBar from "./components/StatsBar";
import TriggerForm from "./components/TriggerForm";
import RunsTable from "./components/RunsTable";
import "./index.css";

export default function App() {
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

  if (!user) {
    return <LoginPage onLogin={refetchUser} onGoogleLogin={login} />;
  }

  function handleTriggerSuccess(result, runName) {
    const newRun = {
      dag_run_id: result.dag_run_id,
      form_url: result.airflow_response?.conf?.form_url ?? "—",
      run_name: runName,
      state: result.state,
      dag_id: result.dag_id,
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
    if (activeTab === "all") return true;
    if (activeTab === "running") return r.state === "running" || r.state === "queued";
    if (activeTab === "done") return r.state === "success";
    if (activeTab === "failed") return r.state === "failed";
    return true;
  });

  return (
    <div className="app">
      <header className="header">
        <span className="logo">former</span>
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
            <button className="logout-btn" onClick={logout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="main main--wide">

        {/* Hero section */}
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

        {/* Trigger card */}
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

        {/* Runs section */}
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
  );
}