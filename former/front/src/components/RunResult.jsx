import { useState } from "react";

const STATE_COLORS = {
  queued: "var(--yellow)",
  running: "var(--blue)",
  success: "var(--green)",
  failed: "var(--red)",
  unknown: "var(--muted)",
};

function stateColor(state) {
  return STATE_COLORS[state] ?? STATE_COLORS.unknown;
}

export default function RunResult({ result }) {
  const [expanded, setExpanded] = useState(false);
  const isMultiple = result.num_executions > 1;

  return (
    <div className="result-card">
      <div className="result-header">
        <span className="result-title">
          {isMultiple ? `${result.num_executions} runs triggered` : "Run triggered"}
        </span>
        <span className="state-badge" style={{ color: stateColor(result.state) }}>
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
        {isMultiple && (
          <>
            <div>
              <dt>Base interval</dt>
              <dd>{result.base_interval_minutes} min</dd>
            </div>
            <div>
              <dt>Jitter</dt>
              <dd>±{result.interval_jitter_minutes} min</dd>
            </div>
          </>
        )}
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