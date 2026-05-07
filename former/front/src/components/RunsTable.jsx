import { useState } from "react";
import RunStageIndicator from "./RunStageIndicator";

const STATE_COLORS = {
  queued: "var(--yellow)",
  running: "var(--blue)",
  success: "var(--green)",
  failed: "var(--red)",
  unknown: "var(--muted)",
};

const AXIS_LABELS = {
  age_profile:       "Age profile",
  political_leaning: "Political leaning",
  risk_tolerance:    "Risk tolerance",
  verbosity:         "Communication",
  formality:         "Formality",
};

function truncate(url, max = 48) {
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

// ── Run detail modal ────────────────────────────────────────
function RunModal({ run, onClose }) {
  const personalityAxes = ["age_profile", "political_leaning", "risk_tolerance", "verbosity", "formality"];
  const hasPersonality = personalityAxes.some((k) => run[k]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div className="modal__title-group">
            <span className="modal__title">{run.run_name}</span>
            <span
              className="state-badge"
              style={{ color: STATE_COLORS[run.state] ?? STATE_COLORS.unknown }}
            >
              {run.state}
            </span>
          </div>
          <button className="modal__close" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>

        <div className="modal__body">

          {/* Stage */}
          <div className="modal__section">
            <span className="modal__section-title">Progress</span>
            <RunStageIndicator state={run.state} />
          </div>

          {/* Core info */}
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

          {/* Executions progress */}
          {run.num_executions > 0 && (() => {
            const completed = run.progress?.completed ?? (run.state === "success" ? run.num_executions : 0);
            const total = run.num_executions;
            const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
            return (
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
                  {run.num_executions > 1 && (
                    <span className="modal__exec-interval">
                      Every {run.base_interval_minutes} min ± {run.interval_jitter_minutes} min
                    </span>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Personality */}
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

// ── Main table ──────────────────────────────────────────────
export default function RunsTable({ runs, loading }) {
  const [selected, setSelected] = useState(null);

  if (loading) return <div className="runs-empty">Loading runs…</div>;

  if (runs.length === 0) {
    return (
      <div className="runs-empty">
        <span>No runs yet.</span>
        <span className="runs-empty__sub">Trigger your first form fill above.</span>
      </div>
    );
  }

  return (
    <>
      <div className="runs-table">
        <div className="runs-table__header">
          <span>Run</span>
          <span>Progress</span>
          <span>Status</span>
          <span>Started</span>
        </div>

        {runs.map((run) => {
          console.log(run);
          return (
            <button
              key={run.dag_run_id ?? run.id}
              className="runs-table__row runs-table__row--btn"
              onClick={() => setSelected(run)}
            >
              <div className="runs-table__name-cell">
                <span className="runs-table__name">{run.run_name || "—"}</span>
                <span className="runs-table__url mono" title={run.form_url}>
                  {truncate(run.form_url)}
                </span>
              </div>

              <RunStageIndicator state={run.state} />

              <span
                className="state-badge"
                style={{ color: STATE_COLORS[run.state] ?? STATE_COLORS.unknown }}
              >
                {run.state}
              </span>

              <span className="runs-table__date">
                {formatDate(run.created_at ?? run.logical_date)}
              </span>
            </button>
          );
        })}
      </div>

      {selected && <RunModal run={selected} onClose={() => setSelected(null)} />}
    </>
  );
}