import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = { online: "#2563eb", offline: "#ef4444", successful: "#16a34a", failed: "#f59e0b" };

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="chart-tooltip">
      <p>{name}: <strong>{value}</strong></p>
    </div>
  );
}

function UptimeDonut({ title, sub, data, colors }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const pct = total > 0 ? ((data[0].value / total) * 100).toFixed(1) : "—";

  return (
    <div className="donut-wrap">
      <h3 className="donut-title">{title}</h3>
      <p className="chart-sub">{sub}</p>
      <div className="donut-center-wrap">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((entry, i) => (
                <Cell key={entry.name} fill={colors[i]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-label">{pct}%</div>
      </div>
    </div>
  );
}

export default function UptimeChart({ speedCounts, connCounts }) {
  return (
    <div className="chart-card">
      <h2 className="chart-title">Uptime Ratio</h2>
      <div className="donut-row">
        <UptimeDonut
          title="Connectivity"
          sub="Checks in selected range"
          data={[
            { name: "Online", value: connCounts.online },
            { name: "Offline", value: connCounts.offline },
          ]}
          colors={[COLORS.online, COLORS.offline]}
        />
        <UptimeDonut
          title="Speedtest"
          sub="Tests in selected range"
          data={[
            { name: "Successful", value: speedCounts.successful },
            { name: "Failed", value: speedCounts.failed },
          ]}
          colors={[COLORS.successful, COLORS.failed]}
        />
      </div>
    </div>
  );
}