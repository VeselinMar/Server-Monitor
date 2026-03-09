import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";
import { format, parseISO } from "date-fns";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}:{" "}
          <strong>
            {p.value != null
              ? p.dataKey === "outage_total_minutes"
                ? `${p.value} min`
                : `${p.value.toFixed(1)} Mbps`
              : "—"}
          </strong>
        </p>
      ))}
    </div>
  );
}

export default function SummaryChart({ summaries }) {
  if (!summaries || summaries.length === 0) {
    return (
      <div className="chart-card">
        <h2 className="chart-title">Historical Summary</h2>
        <p className="chart-sub">No aggregated data available yet.</p>
      </div>
    );
  }

  const data = summaries.map((s) => ({
    date: format(parseISO(s.period_date), "MMM d"),
    avg_download: s.avg_download_mbps,
    avg_upload: s.avg_upload_mbps,
    outage_total_minutes: s.outage_total_minutes || 0,
    min_download: s.min_download_mbps,
  }));

  return (
    <div className="chart-card">
      <h2 className="chart-title">Historical Summary</h2>
      <p className="chart-sub">
        Daily avg download/upload · bars · outage minutes · line
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 48, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#888" }}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="speed"
            tick={{ fontSize: 11, fill: "#888" }}
            unit=" Mbps"
            width={72}
            domain={[0, 120]}
          />
          <YAxis
            yAxisId="outage"
            orientation="right"
            tick={{ fontSize: 11, fill: "#888" }}
            unit=" min"
            width={56}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine
            yAxisId="speed"
            y={75}
            stroke="#16a34a"
            strokeDasharray="4 3"
            strokeWidth={1}
            label={{ value: "75 Mbps min", fontSize: 10, fill: "#16a34a", position: "insideTopRight" }}
          />
          <Bar
            yAxisId="speed"
            dataKey="avg_download"
            name="Avg Download"
            fill="#2563eb"
            opacity={0.85}
            radius={[2, 2, 0, 0]}
          />
          <Bar
            yAxisId="speed"
            dataKey="avg_upload"
            name="Avg Upload"
            fill="#16a34a"
            opacity={0.85}
            radius={[2, 2, 0, 0]}
          />
          <Line
            yAxisId="outage"
            type="monotone"
            dataKey="outage_total_minutes"
            name="Outage minutes"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ r: 3, fill: "#ef4444" }}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}