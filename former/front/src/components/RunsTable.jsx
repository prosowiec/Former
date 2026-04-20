import RunStageIndicator from "./RunStageIndicator";

const STATE_COLORS = {
  queued: "var(--yellow)",
  running: "var(--blue)",
  success: "var(--green)",
  failed: "var(--red)",
  unknown: "var(--muted)",
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

export default function RunsTable({ runs, loading }) {
  if (loading) {
    return <div className="runs-empty">Loading runs…</div>;
  }

  if (runs.length === 0) {
    return (
      <div className="runs-empty">
        <span>No runs yet.</span>
        <span className="runs-empty__sub">Trigger your first form fill above.</span>
      </div>
    );
  }

  return (
    <div className="runs-table">
      <div className="runs-table__header">
        <span>Form</span>
        <span>Progress</span>
        <span>Status</span>
        <span>Started</span>
      </div>

      {runs.map((run) => (
        <div className="runs-table__row" key={run.dag_run_id ?? run.id}>
          <div className="runs-table__name-cell">
            <span className="runs-table__name">{run.run_name || truncate(run.form_url)}</span>
            {run.run_name && (
              <span className="runs-table__url mono" title={run.form_url}>
                {truncate(run.form_url)}
              </span>
            )}
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
        </div>
      ))}
    </div>
  );
}