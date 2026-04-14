import { useState } from "react";
import { api } from "../api/client";

const DEFAULT_DAG_ID = import.meta.env.VITE_DEFAULT_DAG_ID ?? "form_filler_pipeline";

export default function TriggerForm({ setResult, setError }) {
  const [formUrl, setFormUrl] = useState("");
  const [dagId, setDagId] = useState(DEFAULT_DAG_ID);
  const [runId, setRunId] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const payload = { form_url: formUrl, dag_id: dagId };
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
              Run ID <span className="optional">(optional)</span>
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

      <button className="submit-btn" type="submit" disabled={loading}>
        {loading ? <span className="spinner" /> : "Trigger run"}
      </button>
    </form>
  );
}