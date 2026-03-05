import { fmtTimestamp } from "../utils/dates";

function OutageRow({ timestamp, type, reason, color }) {
  return (
    <tr className="outage-row">
      <td className="outage-time">{fmtTimestamp(timestamp)}</td>
      <td>
        <span className="outage-badge" style={{ "--badge-color": color }}>
          {type}
        </span>
      </td>
      <td className="outage-reason">{reason || "—"}</td>
    </tr>
  );
}

export default function OutageTable({ speedFailures, connectivityChecks }) {
  const connOutages = connectivityChecks
    .filter((c) => c.status === "NO INTERNET")
    .map((c) => ({
      timestamp: c.timestamp,
      type: "No Internet",
      reason: "Ping to 8.8.8.8 failed",
      color: "#ef4444",
    }));

  const speedOutages = speedFailures.map((f) => ({
    timestamp: f.timestamp,
    type: "Speedtest Failed",
    reason: f.failure_reason,
    color: "#f59e0b",
  }));

  const all = [...connOutages, ...speedOutages].sort(
    (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
  );

  return (
    <div className="chart-card">
      <h2 className="chart-title">Outage Events</h2>
      <p className="chart-sub">
        {all.length === 0
          ? "No outages in the selected time range."
          : `${all.length} event${all.length !== 1 ? "s" : ""} in selected range`}
      </p>
      {all.length > 0 && (
        <div className="outage-table-wrap">
          <table className="outage-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Type</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {all.map((o, i) => (
                <OutageRow key={i} {...o} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}