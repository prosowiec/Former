import { useState } from "react";
import TriggerForm from "./components/TriggerForm";
import RunResult from "./components/RunResult";
import HealthBadge from "./components/HealthBadge";
import "./index.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  return (
    <div className="app">
      <header className="header">
        <span className="logo">former</span>
        <HealthBadge />
      </header>

      <main className="main">
        <div className="page-title">
          <h1>Trigger a DAG run</h1>
          <p>Submit a form URL to kick off the Airflow pipeline.</p>
        </div>

        <TriggerForm setResult={setResult} setError={setError} />

        {error && (
          <div className="banner banner--error">
            <span className="banner__label">Error</span>
            <span>{error}</span>
          </div>
        )}

        {result && <RunResult result={result} />}
      </main>
    </div>
  );
}