import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import HealthBadge from "./HealthBadge";
import StatsBar from "./StatsBar";
import TriggerForm from "./TriggerForm";
import RunsTable from "./RunsTable";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const {
    filteredRuns, runsLoading, stats,
    TABS, activeTab, setActiveTab,
    handleTriggerSuccess, successBanner,
  } = useDashboard();

  async function handleLogout() {
    await logout();
    navigate("/landing");
  }

  return (
    <div className="app">
      <header className="header">
        <button className="logo logo--btn" onClick={() => navigate("/landing")}>
          former
        </button>
        <div className="header-right">
          <HealthBadge />
          <div className="user-menu">
            {user?.picture && (
              <img
                className="avatar"
                src={user.picture}
                alt={user.name}
                referrerPolicy="no-referrer"
              />
            )}
            <span className="user-name">{user?.name ?? user?.email}</span>
            <button className="logout-btn" onClick={handleLogout}>
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
  );
}