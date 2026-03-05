import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { fmtTimestamp } from "../utils/dates";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{p.value != null ? `${p.value.toFixed(2)} Mbps` : "—"}</strong>
        </p>
      ))}
    </div>
  );
}

export default function SpeedChart({ results, failures }) {
  const data = results.map((r) => ({
    time: fmtTimestamp(r.timestamp),
    download: r.download_mbps,
    upload: r.upload_mbps,
  }));

  const failureMarkers = failures.map((f) => fmtTimestamp(f.timestamp));

  return (
    <div className="chart-card">
      <h2 className="chart-title">Download & Upload Speed</h2>
      <p className="chart-sub">Mbps over time · red markers indicate failed tests</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: "#888" }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 11, fill: "#888" }} unit=" Mbps" width={72} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          {failureMarkers.map((t) => (
            <ReferenceLine key={t} x={t} stroke="#ef4444" strokeDasharray="4 2" strokeWidth={1} />
          ))}
          <Line
            type="monotone"
            dataKey="download"
            name="Download"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="upload"
            name="Upload"
            stroke="#16a34a"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}