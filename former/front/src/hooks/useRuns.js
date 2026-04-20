import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";

export function useRuns() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRuns = useCallback(async () => {
    try {
      const data = await api.getRuns();
      setRuns(data);
    } catch {
      // silently fail — history is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  // Called after a successful trigger to prepend the new run optimistically
  const addRun = useCallback((run) => {
    setRuns((prev) => [run, ...prev]);
  }, []);

  // Update a run's state in place (e.g. after polling)
  const updateRun = useCallback((dag_run_id, patch) => {
    setRuns((prev) =>
      prev.map((r) => (r.dag_run_id === dag_run_id ? { ...r, ...patch } : r))
    );
  }, []);

  const stats = {
    total: runs.length,
    pending: runs.filter((r) => r.state === "queued").length,
    running: runs.filter((r) => r.state === "running").length,
    done: runs.filter((r) => r.state === "success").length,
    failed: runs.filter((r) => r.state === "failed").length,
  };

  return { runs, loading, addRun, updateRun, stats, refetch: fetchRuns };
}