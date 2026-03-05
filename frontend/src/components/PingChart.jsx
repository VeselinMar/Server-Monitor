import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { fmtTimestamp } from "../utils/dates";
import { parseISO as parse, format } from "date-fns";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{p.value != null ? `${p.value.toFixed(1)} ms` : "—"}</strong>
        </p>
      ))}
    </div>
  );
}

export default function PingChart({ speedResults, connectivityChecks }) {
  // Merge both series by timestamp into a unified timeline
  const speedMap = Object.fromEntries(
    speedResults.map((r) => [fmtTimestamp(r.timestamp), r.ping])
  );
  const connMap = Object.fromEntries(
    connectivityChecks
      .filter((c) => c.latency_ms != null)
      .map((c) => [fmtTimestamp(c.timestamp), c.latency_ms])
  );

  const allTimes = Array.from(
    new Set([...Object.keys(speedMap), ...Object.keys(connMap)])
  ).sort();

  const data = allTimes.map((t) => ({
    time: t,
    speedPing: speedMap[t] ?? null,
    connLatency: connMap[t] ?? null,
  }));

  return (
    <div className="chart-card">
      <h2 className="chart-title">Ping & Latency</h2>
      <p className="chart-sub">Milliseconds over time · speedtest ping vs connectivity check RTT</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: "#888" }}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 11, fill: "#888" }} unit=" ms" width={56} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="speedPing"
            name="Speedtest ping"
            stroke="#7c3aed"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="connLatency"
            name="Connectivity RTT"
            stroke="#db2777"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}