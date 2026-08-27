import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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
  const values = data
    .map((point) => point.latency)
    .filter(
      (value) => Number.isFinite(value) && value >= 0
    );

  if (!values.length) {
    return [0, 100];
  }

  const p95 = percentile(values, 0.95);

  if (!Number.isFinite(p95) || p95 <= 0) {
    return [0, 100];
  }

  return [0, Math.max(p95 * 1.2, 10)];
};

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>

      <p style={{ color: "#db2777" }}>
        Connectivity RTT:{" "}
        <strong>
          {payload[0].value != null
            ? `${payload[0].value.toFixed(1)} ms`
            : "—"}
        </strong>
      </p>
    </div>
  );
}

export default function PingChart({ connectivityChecks }) {
  const data = connectivityChecks
    .filter(
      (c) =>
        c.latency_ms != null &&
        Number.isFinite(Number(c.latency_ms))
    )
    .map((c) => ({
      time: fmtTimestamp(c.timestamp),
      ts: new Date(c.timestamp),
      latency: Number(c.latency_ms),
    }))
    .sort((a, b) => a.ts - b.ts);

  const latencyDomain = getLatencyDomain(data);

  return (
    <div className="chart-card">
      <h2 className="chart-title">Ping & Latency</h2>

      <p className="chart-sub">
        Connectivity round-trip time over the selected period
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

          <Line
            type="monotone"
            dataKey="latency"
            name="Connectivity RTT"
            stroke="#db2777"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
