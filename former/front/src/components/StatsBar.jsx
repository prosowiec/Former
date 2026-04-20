export default function StatsBar({ stats }) {
  const items = [
    { label: "Total runs", value: stats.total, color: "var(--text)" },
    { label: "Running", value: stats.running, color: "var(--blue)" },
    { label: "Done", value: stats.done, color: "var(--green)" },
    { label: "Failed", value: stats.failed, color: "var(--red)" },
  ];

  return (
    <div className="stats-bar">
      {items.map(({ label, value, color }) => (
        <div className="stat-item" key={label}>
          <span className="stat-value" style={{ color }}>{value}</span>
          <span className="stat-label">{label}</span>
        </div>
      ))}
    </div>
  );
}