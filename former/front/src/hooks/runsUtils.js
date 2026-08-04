export function normalizeRuns(runs) {
  if (Array.isArray(runs)) return runs;
  if (runs && typeof runs === "object" && Array.isArray(runs.runs)) {
    return runs.runs;
  }
  return [];
}

export function formatFillRate(intervalMinutes) {
  const minutes = Number(intervalMinutes);
  if (!Number.isFinite(minutes) || minutes <= 0) return "Pace unavailable";

  const useDays = minutes >= 60;
  const periodMinutes = useDays ? 24 * 60 : 60;
  const rawRate = periodMinutes / minutes;
  const rate = Number.isInteger(rawRate) ? rawRate : Number(rawRate.toFixed(1));
  const unit = useDays ? "day" : "hour";
  return `${rate} ${rate === 1 ? "form" : "forms"} per ${unit}`;
}
