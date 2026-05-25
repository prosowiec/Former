import { useState } from "react";
import { useRuns } from "./useRuns";

const TABS = [
  { id: "all",     label: "All" },
  { id: "running", label: "Running" },
  { id: "done",    label: "Done" },
  { id: "failed",  label: "Failed" },
];

export function useDashboard() {
  const { runs, loading: runsLoading, addRun, updateRun, stats } = useRuns();
  const [successBanner, setSuccessBanner] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  function handleTriggerSuccess(result, runName) {
    const newRun = {
      dag_run_id:             result.dag_run_id,
      form_url:               result.airflow_response?.conf?.form_url ?? "—",
      run_name:               runName,
      state:                  result.state,
      dag_id:                 result.dag_id,
      num_executions:         result.num_executions,
      base_interval_minutes:  result.base_interval_minutes,
      interval_jitter_minutes: result.interval_jitter_minutes,
      created_at:             new Date().toISOString(),
    };
    addRun(newRun);
    setSuccessBanner(`"${runName}" triggered successfully`);
    setTimeout(() => setSuccessBanner(null), 4000);
  }

  const filteredRuns = runs.filter((r) => {
    if (activeTab === "running") return r.state === "running" || r.state === "queued";
    if (activeTab === "done")    return r.state === "success";
    if (activeTab === "failed")  return r.state === "failed";
    return true;
  });

  function handleRunCancelled(dag_run_id) {
    updateRun(dag_run_id, { state: "failed" });
  }

  return {
    filteredRuns,
    runsLoading,
    stats,
    TABS,
    activeTab,
    setActiveTab,
    handleTriggerSuccess,
    handleRunCancelled,
    successBanner,
  };
}