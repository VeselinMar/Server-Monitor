export default function StatCard({ label, value, unit, sub, accent }) {
  return (
    <div className="stat-card" style={{ "--accent": accent }}>
      <span className="stat-label">{label}</span>
      <div className="stat-value">
        {value ?? <span className="stat-null">—</span>}
        {unit && value != null && <span className="stat-unit">{unit}</span>}
      </div>
      {sub && <span className="stat-sub">{sub}</span>}
    </div>
  );
}