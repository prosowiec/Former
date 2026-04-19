import { useState } from "react";
import { api } from "../api/client";

const DEFAULT_DAG_ID = import.meta.env.VITE_DEFAULT_DAG_ID ?? "form_filler_pipeline";

export default function TriggerForm({ setResult, setError, user }) {
  const [formUrl, setFormUrl] = useState("");
  const [dagId, setDagId] = useState(DEFAULT_DAG_ID);
  const [runId, setRunId] = useState("");
  const [numExecutions, setNumExecutions] = useState(2);
  const [baseInterval, setBaseInterval] = useState(2);
  const [jitter, setJitter] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isMultiple = numExecutions > 1;
  const isAuthenticated = Boolean(user);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!isAuthenticated) {
      setError("Please sign in with Google before triggering a DAG.");
      return;
    }
    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const payload = {
        form_url: formUrl,
        dag_id: dagId,
        num_executions: numExecutions,
        base_interval_minutes: baseInterval,
        interval_jitter_minutes: jitter,
      };
      if (runId.trim()) payload.run_id = runId.trim();

      const data = await api.trigger(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="trigger-form" onSubmit={handleSubmit} noValidate>
      <div className="field">
        <label htmlFor="form_url">Form URL</label>
        <input
          id="form_url"
          type="url"
          placeholder="https://example.com/form"
          value={formUrl}
          onChange={(e) => setFormUrl(e.target.value)}
          required
          autoFocus
        />
      </div>

      <div className="field">
        <label htmlFor="num_executions">Number of executions</label>
        <input
          id="num_executions"
          type="number"
          min={1}
          value={numExecutions}
          onChange={(e) => setNumExecutions(Number(e.target.value))}
        />
      </div>

      {isMultiple && (
        <div className="field-row">
          <div className="field">
            <label htmlFor="base_interval">
              Base interval <span className="optional">(minutes)</span>
            </label>
            <input
              id="base_interval"
              type="number"
              min={0}
              value={baseInterval}
              onChange={(e) => setBaseInterval(Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label htmlFor="jitter">
              Jitter <span className="optional">(minutes)</span>
            </label>
            <input
              id="jitter"
              type="number"
              min={0}
              value={jitter}
              onChange={(e) => setJitter(Number(e.target.value))}
            />
          </div>
        </div>
      )}

      <button
        type="button"
        className="advanced-toggle"
        onClick={() => setShowAdvanced((v) => !v)}
      >
        {showAdvanced ? "Hide" : "Show"} advanced options
      </button>

      {showAdvanced && (
        <div className="advanced-fields">
          <div className="field">
            <label htmlFor="dag_id">DAG ID</label>
            <input
              id="dag_id"
              type="text"
              value={dagId}
              onChange={(e) => setDagId(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="run_id">
              Run ID prefix <span className="optional">(optional)</span>
            </label>
            <input
              id="run_id"
              type="text"
              placeholder="manual__2024-01-01"
              value={runId}
              onChange={(e) => setRunId(e.target.value)}
            />
          </div>
        </div>
      )}

      <button className="submit-btn" type="submit" disabled={loading || !isAuthenticated}>
        {loading ? (
          <span className="spinner" />
        ) : isMultiple ? (
          `Trigger ${numExecutions} runs`
        ) : (
          "Trigger run"
        )}
      </button>
      {!isAuthenticated && (
        <div className="banner banner--info">
          Please sign in with Google before triggering a DAG.
        </div>
      )}
    </form>
  );
}