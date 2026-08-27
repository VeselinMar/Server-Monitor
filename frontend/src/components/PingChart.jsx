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

const percentile = (values, p) => {
  const sorted = values
    .filter((value) => Number.isFinite(value))
    .slice()
    .sort((a, b) => a - b);

  if (!sorted.length) return null;

  const index = (sorted.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);

  if (lower === upper) {
    return sorted[lower];
  }

  return (
    sorted[lower] +
    (sorted[upper] - sorted[lower]) * (index - lower)
  );
};

const getLatencyDomain = (data) => {
  const values = data.flatMap((point) => [
    point.speedPing,
    point.connLatency,
  ]);

  const clean = values.filter(
    (value) => Number.isFinite(value) && value >= 0
  );

  if (!clean.length) {
    return [0, 100];
  }

  // Ignore extreme outliers when determining the visual scale.
  const p95 = percentile(clean, 0.95);

  if (!Number.isFinite(p95) || p95 <= 0) {
    return [0, 100];
  }

  // Give the chart some breathing room above the normal range.
  const upper = Math.max(p95 * 1.2, 10);

  return [0, upper];
};

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>

      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}:{" "}
          <strong>
            {p.value != null ? `${p.value.toFixed(1)} ms` : "—"}
          </strong>
        </p>
      ))}
    </div>
  );
}

export default function PingChart({
  speedResults,
  connectivityChecks,
}) {
  const merged = [
    ...speedResults.map((r) => ({
      time: fmtTimestamp(r.timestamp),
      ts: new Date(r.timestamp),
      speedPing: r.ping,
      connLatency: null,
    })),

    ...connectivityChecks
      .filter((c) => c.latency_ms != null)
      .map((c) => ({
        time: fmtTimestamp(c.timestamp),
        ts: new Date(c.timestamp),
        speedPing: null,
        connLatency: c.latency_ms,
      })),
  ].sort((a, b) => a.ts - b.ts);

  // Merge entries with the same formatted timestamp.
  const seen = new Map();

  for (const entry of merged) {
    if (!seen.has(entry.time)) {
      seen.set(entry.time, {
        time: entry.time,
        speedPing: null,
        connLatency: null,
      });
    }

    const point = seen.get(entry.time);

    if (entry.speedPing != null) {
      point.speedPing = entry.speedPing;
    }

    if (entry.connLatency != null) {
      point.connLatency = entry.connLatency;
    }
  }

  const data = Array.from(seen.values());

  // Calculate the scale from the actual displayed data.
  // A single extreme outage therefore won't flatten the normal graph.
  const latencyDomain = getLatencyDomain(data);

  return (
    <div className="chart-card">
      <h2 className="chart-title">Ping & Latency</h2>

      <p className="chart-sub">
        Milliseconds over time · speedtest ping vs connectivity check RTT
      </p>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart
          data={data}
          margin={{
            top: 8,
            right: 16,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e8e8e8"
          />

          <XAxis
            dataKey="time"
            tick={{
              fontSize: 11,
              fill: "#888",
            }}
            interval="preserveStartEnd"
          />

          <YAxis
            domain={latencyDomain}
            tick={{
              fontSize: 11,
              fill: "#888",
            }}
            unit=" ms"
            width={56}
          />

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
