import { useState } from "react";
import RunStageIndicator from "./RunStageIndicator";
import { api } from "../api/client";

const STATE_COLORS = {
  queued:    "var(--yellow)",
  running:   "var(--blue)",
  success:   "var(--green)",
  failed:    "var(--red)",
  cancelled: "var(--muted)",
  unknown:   "var(--muted)",
};

const AXIS_LABELS = {
  age_profile:       "Age profile",
  political_leaning: "Political leaning",
  risk_tolerance:    "Risk tolerance",
  verbosity:         "Communication",
  formality:         "Formality",
};

const CANCELLABLE = new Set(["queued", "running"]);

function truncate(url, max = 44) {
  if (!url) return "—";
  try {
    const u = new URL(url);
    const path = u.hostname + u.pathname;
    return path.length > max ? path.slice(0, max) + "…" : path;
  } catch {
    return url.length > max ? url.slice(0, max) + "…" : url;
  }
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function humanize(val) {
  if (!val) return "—";
  return val.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Cancel confirm modal ─────────────────────────────────────
function CancelModal({ run, onClose, onConfirmed }) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  async function doCancel() {
    setError(null);
    setLoading(true);
    try {
      await api.cancelRun(run.dag_run_id);
      onConfirmed(run.dag_run_id);
    } catch (err) {
      setError(err.message ?? "Failed to cancel run.");
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal cancel-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div className="modal__title-group">
            <span className="modal__title">Cancel run?</span>
          </div>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        <div className="modal__body">
          <p className="cancel-modal__desc">
            This will stop <strong>{run.run_name || run.dag_run_id}</strong>.
            Any in-progress form fills may be left incomplete.
          </p>

          {error && (
            <div className="banner banner--error">
              <span className="banner__label">Error</span>
              <span>{error}</span>
            </div>
          )}

          <div className="cancel-modal__actions">
            <button className="cancel-modal__keep" onClick={onClose} disabled={loading}>
              Keep running
            </button>
            <button className="cancel-modal__confirm" onClick={doCancel} disabled={loading}>
              {loading ? <span className="spinner" /> : "Yes, cancel"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Execution count badge ─────────────────────────────────────
function ExecBadge({ run }) {
  const total     = run.num_executions ?? 1;
  const completed = run.progress?.numberOfSuccessfulRuns ?? (run.state === "success" ? total : 0);
  if (total <= 1) return null;
  return (
    <span className="exec-badge" title={`${completed} of ${total} executions done`}>
      {completed}/{total}
    </span>
  );
}

// ── Run detail modal ─────────────────────────────────────────
function RunModal({ run, onClose, onCancelRequest }) {
  const personalityAxes = ["age_profile", "political_leaning", "risk_tolerance", "verbosity", "formality"];
  const hasPersonality  = personalityAxes.some((k) => run[k]);
  const total           = run.num_executions ?? 0;
  const completed       = run.progress?.numberOfSuccessfulRuns ?? (run.state === "success" ? total : 0);
  const pct             = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>

        <div className="modal__header">
          <div className="modal__title-group">
            <span className="modal__title">{run.run_name}</span>
            <span className="state-badge" style={{ color: STATE_COLORS[run.state] ?? STATE_COLORS.unknown }}>
              {run.state}
            </span>
          </div>
          <div className="modal__header-actions">
            {CANCELLABLE.has(run.state) && (
              <button
                className="modal__cancel-btn"
                onClick={() => { onClose(); onCancelRequest(run); }}
              >
                Cancel run
              </button>
            )}
            <button className="modal__close" onClick={onClose} aria-label="Close">
              <CloseIcon />
            </button>
          </div>
        </div>

        <div className="modal__body">

          <div className="modal__section">
            <span className="modal__section-title">Progress</span>
            <RunStageIndicator state={run.state} />
          </div>

          <div className="modal__section">
            <span className="modal__section-title">Run details</span>
            <dl className="modal__dl">
              <div className="modal__dl-row">
                <dt>Form URL</dt>
                <dd>
                  <a href={run.form_url} target="_blank" rel="noopener noreferrer" className="modal__link mono">
                    {truncate(run.form_url, 60)}
                  </a>
                </dd>
              </div>
              <div className="modal__dl-row">
                <dt>Started</dt>
                <dd>{formatDate(run.created_at)}</dd>
              </div>
            </dl>
          </div>

          {total > 0 && (
            <div className="modal__section">
              <span className="modal__section-title">Executions</span>
              <div className="modal__exec">
                <div className="modal__exec-meta">
                  <span className="modal__exec-count">{completed} / {total}</span>
                  <span className="modal__exec-pct">{pct}%</span>
                </div>
                <div className="modal__exec-track">
                  <div
                    className={`modal__exec-fill${run.state === "failed" ? " modal__exec-fill--failed" : ""}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                {total > 1 && (
                  <span className="modal__exec-interval">
                    Every {run.base_interval_minutes} min ± {run.interval_jitter_minutes} min
                  </span>
                )}
              </div>
            </div>
          )}

          {hasPersonality && (
            <div className="modal__section">
              <span className="modal__section-title">Agent personality</span>
              <div className="modal__personality">
                {personalityAxes.map((key) => run[key] ? (
                  <div className="modal__personality-row" key={key}>
                    <span className="modal__personality-axis">{AXIS_LABELS[key]}</span>
                    <span className="trait-tag">{humanize(run[key])}</span>
                  </div>
                ) : null)}
              </div>
            </div>
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

// ── Main table ───────────────────────────────────────────────
export default function RunsTable({ runs, loading, onRunCancelled }) {
  const [selected,     setSelected]     = useState(null);
  const [cancelTarget, setCancelTarget] = useState(null);

  if (loading) return <div className="runs-empty">Loading runs…</div>;

  if (runs.length === 0) {
    return (
      <div className="runs-empty">
        <span>No runs yet.</span>
        <span className="runs-empty__sub">Trigger your first form fill above.</span>
      </div>
    );
  }

  function handleCancelConfirmed(dag_run_id) {
    setCancelTarget(null);
    onRunCancelled?.(dag_run_id);
  }

  return (
    <>
      <div className="runs-table">
        <div className="runs-table__header">
          <span>Run</span>
          <span>Progress</span>
          <span>Status</span>
          <span>Started</span>
          <span />
        </div>

        {runs.map((run) => {
          const cancellable = CANCELLABLE.has(run.state);
          return (
            <button
              key={run.dag_run_id ?? run.id}
              className="runs-table__row runs-table__row--btn"
              onClick={() => setSelected(run)}
            >
              <div className="runs-table__name-cell">
                <div className="runs-table__name-row">
                  <span className="runs-table__name">{run.run_name || "—"}</span>
                  <ExecBadge run={run} />
                </div>
                <span className="runs-table__url mono" title={run.form_url}>
                  {truncate(run.form_url)}
                </span>
              </div>

              <RunStageIndicator state={run.state} />

              <span className="state-badge" style={{ color: STATE_COLORS[run.state] ?? STATE_COLORS.unknown }}>
                {run.state}
              </span>

              <span className="runs-table__date">
                {formatDate(run.created_at ?? run.logical_date)}
              </span>

              <span className="runs-table__actions" onClick={(e) => e.stopPropagation()}>
                {cancellable && (
                  <button
                    className="run-cancel-btn"
                    onClick={(e) => { e.stopPropagation(); setCancelTarget(run); }}
                  >
                    Cancel
                  </button>
                )}
              </span>
            </button>
          );
        })}
      </div>

      {selected && (
        <RunModal
          run={selected}
          onClose={() => setSelected(null)}
          onCancelRequest={(run) => { setSelected(null); setCancelTarget(run); }}
        />
      )}

      {cancelTarget && (
        <CancelModal
          run={cancelTarget}
          onClose={() => setCancelTarget(null)}
          onConfirmed={handleCancelConfirmed}
        />
      )}
    </>
  );
}