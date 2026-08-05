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

export function formatExpectedFillEnd(startTime, totalFills, intervalMinutes) {
  const start = new Date(startTime);
  const fills = Math.max(1, Number(totalFills) || 1);
  const interval = Number(intervalMinutes);
  if (Number.isNaN(start.getTime()) || !Number.isFinite(interval) || interval <= 0) {
    return "Unavailable";
  }

  const expectedEnd = new Date(start.getTime() + fills * interval * 60_000);
  return formatBrowserDateTime(expectedEnd);
}

export function formatBrowserDateTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unavailable";

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}
