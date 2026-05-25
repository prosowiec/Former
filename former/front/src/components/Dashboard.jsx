import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import { useBilling } from "../hooks/useBilling";
import HealthBadge from "./HealthBadge";
import TriggerForm from "./TriggerForm";
import RunsTable from "./RunsTable";
import BillingModal from "./BillingModal";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [billingOpen, setBillingOpen] = useState(false);
  const {
    filteredRuns, runsLoading, stats,
    TABS, activeTab, setActiveTab,
    handleTriggerSuccess, handleRunCancelled, successBanner,
  } = useDashboard();
  const { billing } = useBilling();

  const fillsRemaining = billing?.form_fills_remaining ?? null;
  const fillsUsed      = billing?.form_fills_used      ?? null;
  const lowFills = fillsRemaining !== null && fillsRemaining < 10;

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

          {/* Fills counter + top-up — always visible */}
          <button
            className={`fills-btn${lowFills ? " fills-btn--low" : ""}`}
            onClick={() => setBillingOpen(true)}
          >
            <span className="fills-btn__count">
              {fillsRemaining !== null ? fillsRemaining : "—"}
            </span>
            <span className="fills-btn__label">fills left</span>
            <span className="fills-btn__cta">Top up</span>
          </button>

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

        {/* Hero — clean, no stats */}
        <div className="dashboard-hero">
          <div className="dashboard-hero__text">
            <h1>Form filler</h1>
            <p>
              Submit a university form URL and let the LLM pipeline handle the rest —
              fetching, filling, and submitting automatically.
            </p>
          </div>
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

        {/* Runs card — stats live here now */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">Runs</span>
            <div className="card__header-right">
              {/* Run stats inline */}
              <div className="run-stats">
                <span className="run-stat">
                  <span className="run-stat__val">{stats.total}</span>
                  <span className="run-stat__label">Total</span>
                </span>
                <span className="run-stat run-stat--blue">
                  <span className="run-stat__val">{stats.running}</span>
                  <span className="run-stat__label">Running</span>
                </span>
                <span className="run-stat run-stat--green">
                  <span className="run-stat__val">{stats.done}</span>
                  <span className="run-stat__label">Done</span>
                </span>
                <span className="run-stat run-stat--red">
                  <span className="run-stat__val">{stats.failed}</span>
                  <span className="run-stat__label">Failed</span>
                </span>
              </div>

              <div className="card__divider" />

              {/* Tabs */}
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
          </div>

          {/* Fills usage bar */}
          {fillsRemaining !== null && (
            <div className="fills-usage">
              <div className="fills-usage__meta">
                <span className="fills-usage__label">
                  Form fills
                  {lowFills && <span className="fills-usage__warning"> · Running low</span>}
                </span>
                <span className="fills-usage__numbers">
                  <span className="fills-usage__remaining">{fillsRemaining} remaining</span>
                  <span className="fills-usage__sep">·</span>
                  <span className="fills-usage__used">{fillsUsed} used</span>
                  <button className="fills-usage__topup" onClick={() => setBillingOpen(true)}>
                    Top up →
                  </button>
                </span>
              </div>
              {(() => {
                const total = fillsRemaining + fillsUsed;
                const pct = total > 0 ? Math.round((fillsRemaining / total) * 100) : 0;
                return (
                  <div className="fills-usage__track">
                    <div
                      className={`fills-usage__bar${lowFills ? " fills-usage__bar--low" : ""}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                );
              })()}
            </div>
          )}

          <RunsTable runs={filteredRuns} loading={runsLoading} onRunCancelled={handleRunCancelled} />
        </div>
      </main>

      {billingOpen && <BillingModal onClose={() => setBillingOpen(false)} />}
    </div>
  );
}