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
  ReferenceArea,
} from "recharts";
import { fmtTimestamp } from "../utils/dates";

const STATUS_COLOR = {
  NORMAL: "#16a34a",
  DEGRADED: "#f59e0b",
  CRITICAL: "#ef4444",
};

function CustomDot({ cx, cy, payload }) {
  const color = STATUS_COLOR[payload.performance_status] || STATUS_COLOR.NORMAL;
  return <circle cx={cx} cy={cy} r={3} fill={color} stroke="white" strokeWidth={1} />;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const status = payload[0]?.payload?.performance_status;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{p.value != null ? `${p.value.toFixed(2)} Mbps` : "—"}</strong>
        </p>
      ))}
      {status && (
        <p style={{ color: STATUS_COLOR[status], marginTop: 4, fontSize: 11 }}>
          ● {status}
        </p>
      )}
    </div>
  );
}

export default function SpeedChart({ results, failures }) {
  const data = results.map((r) => ({
    time: fmtTimestamp(r.timestamp),
    download: r.download_mbps,
    upload: r.upload_mbps,
    performance_status: r.performance_status,
  }));

  const failureMarkers = failures.map((f) => fmtTimestamp(f.timestamp));

  return (
    <div className="chart-card">
      <h2 className="chart-title">Download & Upload Speed</h2>
      <p className="chart-sub">
        Mbps over time · dots coloured by performance status ·
        <span style={{ color: STATUS_COLOR.NORMAL }}> ● Normal</span>
        <span style={{ color: STATUS_COLOR.DEGRADED }}> ● Degraded</span>
        <span style={{ color: STATUS_COLOR.CRITICAL }}> ● Critical</span>
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          <ReferenceArea y1={0} y2={30} fill="#ef444408" />
          <ReferenceArea y1={30} y2={75} fill="#f59e0b08" />
          <ReferenceArea y1={75} y2={160} fill="#16a34a06" />
          <ReferenceLine
            y={75}
            stroke="#16a34a"
            strokeDasharray="4 3"
            strokeWidth={1}
            label={{ value: "75 Mbps min", fontSize: 10, fill: "#16a34a", position: "insideTopRight" }}
          />
          <ReferenceLine
            y={30}
            stroke="#ef4444"
            strokeDasharray="4 3"
            strokeWidth={1}
            label={{ value: "30 Mbps critical", fontSize: 10, fill: "#ef4444", position: "insideTopRight" }}
          />
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
            dot={<CustomDot />}
            activeDot={{ r: 5 }}
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