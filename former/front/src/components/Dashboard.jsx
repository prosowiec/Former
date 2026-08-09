import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import { useBilling } from "../hooks/useBilling";
import { api } from "../api/client";
import TriggerForm from "./TriggerForm";
import RunsTable from "./RunsTable";
import Billingmodal from "./Billingmodal";
import ProfileModal from "./ProfileModal";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [billingOpen, setBillingOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null); // "success" | "error" | null
  const {
    filteredRuns, runsLoading, refreshRuns, stats,
    TABS, activeTab, setActiveTab,
    handleTriggerSuccess, handleRunCancelled, successBanner,
  } = useDashboard();
  const { billing, refetch: refetchBilling } = useBilling();

  const fillsRemaining = billing?.form_fills_remaining ?? null;
  const fillsUsed      = billing?.form_fills_used      ?? null;

  // Handle Stripe redirect return (PayPal, bank redirect, etc.)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paymentIntentId = params.get("payment_intent");
    const redirectStatus  = params.get("redirect_status");

    if (!paymentIntentId || redirectStatus !== "succeeded") return;

    // Clean URL immediately so a refresh doesn't re-trigger
    window.history.replaceState({}, document.title, window.location.pathname);

    api.confirmPayment({
      payment_intent_id: paymentIntentId,
    })
      .then(() => {
        refetchBilling();
        setPaymentStatus("success");
      })
      .catch(() => {
        setPaymentStatus("error");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleLogout() {
    await logout();
    navigate("/landing");
  }

  async function handleSessionEnded() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app">
      <header className="header">
        <button className="logo logo--btn" onClick={() => navigate("/landing")}>
          former
        </button>
        <div className="header-right">
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
            <button className="logout-btn" onClick={() => setProfileOpen(true)}>
              Profile
            </button>
            <button className="logout-btn" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="main main--wide">

        {paymentStatus === "success" && (
          <div className="banner banner--success">
            <span className="banner__label">Payment confirmed</span>
            <span>Your fills have been added to your account.</span>
            <button
              style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "inherit", fontSize: "16px" }}
              onClick={() => setPaymentStatus(null)}
            >×</button>
          </div>
        )}
        {paymentStatus === "error" && (
          <div className="banner banner--error">
            <span className="banner__label">Payment error</span>
            <span>Could not confirm your payment. Please contact support.</span>
            <button
              style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "inherit", fontSize: "16px" }}
              onClick={() => setPaymentStatus(null)}
            >×</button>
          </div>
        )}

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
          <TriggerForm
            onSuccess={handleTriggerSuccess}
            fillsRemaining={fillsRemaining}
            onTopUp={() => setBillingOpen(true)}
          />
        </div>

        {/* Runs card — stats live here now */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">Runs</span>
            <div className="card__header-right runs-toolbar">
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
              <div className="tabs runs-filters">
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

              <div className="card__divider" />

              <button
                type="button"
                className="runs-refresh-btn"
                onClick={refreshRuns}
                disabled={runsLoading}
                aria-label={runsLoading ? "Refreshing runs" : "Refresh runs"}
              >
                <RefreshIcon spinning={runsLoading} />
                {runsLoading ? "Refreshing" : "Refresh"}
              </button>
            </div>
          </div>

          {/* Fills usage bar */}
          {fillsRemaining !== null && (
            <div className="fills-usage">
              <div className="fills-usage__meta">
                <span className="fills-usage__label">
                  Form fills
                  {fillsRemaining !== null && fillsRemaining < 10 && <span className="fills-usage__warning"> · Running low</span>}
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
                      className={`fills-usage__bar${fillsRemaining !== null && fillsRemaining < 10 ? " fills-usage__bar--low" : ""}`}
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

      {billingOpen && <Billingmodal onClose={() => { setBillingOpen(false); refetchBilling(); }} />}
      {profileOpen && (
        <ProfileModal
          user={user}
          onClose={() => setProfileOpen(false)}
          onTopUp={() => { setProfileOpen(false); setBillingOpen(true); }}
          onSessionEnded={handleSessionEnded}
        />
      )}
    </div>
  );
}

function RefreshIcon({ spinning = false }) {
  return (
    <svg
      className={spinning ? "runs-refresh-icon runs-refresh-icon--spinning" : "runs-refresh-icon"}
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M20 11a8 8 0 1 0-2.34 5.66M20 4v7h-7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
