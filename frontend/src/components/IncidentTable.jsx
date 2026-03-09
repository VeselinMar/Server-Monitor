import { fmtTimestamp } from "../utils/dates";

const TYPE_CONFIG = {
  FAILURE:  { label: "Test Failed",  color: "#ef4444" },
  CRITICAL: { label: "Critical",     color: "#dc2626" },
  DEGRADED: { label: "Degraded",     color: "#f59e0b" },
  "NO INTERNET": { label: "No Internet", color: "#7c3aed" },
};

function duration(minutes) {
  if (minutes < 1) return "< 1 min";
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export default function IncidentTable({ incidents }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="chart-card">
        <h2 className="chart-title">Incidents</h2>
        <p className="chart-sub">No incidents in the selected time range.</p>
      </div>
    );
  }

  const sorted = [...incidents].sort((a, b) => new Date(b.start) - new Date(a.start));

  return (
    <div className="chart-card">
      <h2 className="chart-title">Incidents</h2>
      <p className="chart-sub">
        {sorted.length} incident{sorted.length !== 1 ? "s" : ""} in selected range ·
        outages, failures, and degradation events
      </p>
      <div className="outage-table-wrap">
        <table className="outage-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Start</th>
              <th>End</th>
              <th>Duration</th>
              <th>Avg Down</th>
              <th>Avg Up</th>
              <th>Avg Ping</th>
              <th>Samples</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((inc, i) => {
              const cfg = TYPE_CONFIG[inc.type] || { label: inc.type, color: "#888" };
              return (
                <tr className="outage-row" key={i}>
                  <td>
                    <span className="outage-badge" style={{ "--badge-color": cfg.color }}>
                      {cfg.label}
                    </span>
                  </td>
                  <td className="outage-time">{fmtTimestamp(inc.start)}</td>
                  <td className="outage-time">{fmtTimestamp(inc.end)}</td>
                  <td className="outage-time">{duration(inc.duration_minutes)}</td>
                  <td className="outage-time">
                    {inc.avg_download_mbps != null ? `${inc.avg_download_mbps} Mbps` : "—"}
                  </td>
                  <td className="outage-time">
                    {inc.avg_upload_mbps != null ? `${inc.avg_upload_mbps} Mbps` : "—"}
                  </td>
                  <td className="outage-time">
                    {inc.avg_ping != null ? `${inc.avg_ping} ms` : "—"}
                  </td>
                  <td className="outage-time">{inc.sample_count}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}