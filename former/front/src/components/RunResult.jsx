import { useState } from "react";

const STATE_COLORS = {
  queued: "var(--yellow)",
  running: "var(--blue)",
  success: "var(--green)",
  failed: "var(--red)",
  unknown: "var(--muted)",
};

export default function RunResult({ result }) {
  const [expanded, setExpanded] = useState(false);
  const stateColor = STATE_COLORS[result.state] ?? STATE_COLORS.unknown;

  return (
    <div className="result-card">
      <div className="result-header">
        <span className="result-title">Run triggered</span>
        <span className="state-badge" style={{ color: stateColor }}>
          {result.state}
        </span>
      </div>

      <dl className="result-meta">
        <div>
          <dt>DAG</dt>
          <dd>{result.dag_id}</dd>
        </div>
        <div>
          <dt>Run ID</dt>
          <dd className="mono">{result.dag_run_id || "—"}</dd>
        </div>
      </dl>

      <button
        className="advanced-toggle"
        onClick={() => setExpanded((v) => !v)}
      >
        {expanded ? "Hide" : "Show"} raw response
      </button>

      {expanded && (
        <pre className="raw-response">
          {JSON.stringify(result.airflow_response, null, 2)}
        </pre>
      )}
    </div>
  );
}