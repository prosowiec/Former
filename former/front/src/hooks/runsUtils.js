export function normalizeRuns(runs) {
  if (Array.isArray(runs)) return runs;
  if (runs && typeof runs === "object" && Array.isArray(runs.runs)) {
    return runs.runs;
  }
  return [];
}
