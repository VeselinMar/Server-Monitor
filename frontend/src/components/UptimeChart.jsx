import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = {
  online:     { fill: "#2563eb", bg: "#eff6ff", label: "Online" },
  offline:    { fill: "#ef4444", bg: "#fef2f2", label: "Offline" },
  successful: { fill: "#16a34a", bg: "#f0fdf4", label: "Successful" },
  failed:     { fill: "#f59e0b", bg: "#fffbeb", label: "Failed" },
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="chart-tooltip">
      <p>{name}: <strong>{value}</strong></p>
    </div>
  );
}

function UptimeDonut({ title, primary, secondary, primaryKey, secondaryKey }) {
  const total = primary + secondary;
  const pct = total > 0 ? ((primary / total) * 100).toFixed(1) : "—";
  const primaryCfg = COLORS[primaryKey];
  const secondaryCfg = COLORS[secondaryKey];

  const data = [
    { name: primaryCfg.label, value: primary },
    { name: secondaryCfg.label, value: secondary },
  ];

  return (
    <div className="uptime-donut">
      <div className="uptime-donut-chart">
        <ResponsiveContainer width={140} height={140}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={46}
              outerRadius={64}
              paddingAngle={2}
              dataKey="value"
              startAngle={90}
              endAngle={-270}
            >
              <Cell fill={primaryCfg.fill} />
              <Cell fill={secondaryCfg.fill} />
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="uptime-pct">{pct}%</div>
      </div>
      <div className="uptime-donut-info">
        <p className="uptime-donut-title">{title}</p>
        <div className="uptime-legend">
          <div className="uptime-legend-item">
            <span className="uptime-legend-dot" style={{ background: primaryCfg.fill }} />
            <span className="uptime-legend-label">{primaryCfg.label}</span>
            <span className="uptime-legend-count">{primary}</span>
          </div>
          <div className="uptime-legend-item">
            <span className="uptime-legend-dot" style={{ background: secondaryCfg.fill }} />
            <span className="uptime-legend-label">{secondaryCfg.label}</span>
            <span className="uptime-legend-count">{secondary}</span>
          </div>
          <div className="uptime-legend-item uptime-legend-total">
            <span className="uptime-legend-label">Total</span>
            <span className="uptime-legend-count">{total}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function UptimeChart({ speedCounts, connCounts }) {
  return (
    <div className="chart-card">
      <h2 className="chart-title">Uptime Ratio</h2>
      <p className="chart-sub">Selected time range</p>
      <div className="uptime-row">
        <UptimeDonut
          title="Connectivity"
          primary={connCounts.online}
          secondary={connCounts.offline}
          primaryKey="online"
          secondaryKey="offline"
        />
        <div className="uptime-divider" />
        <UptimeDonut
          title="Speedtest"
          primary={speedCounts.successful}
          secondary={speedCounts.failed}
          primaryKey="successful"
          secondaryKey="failed"
        />
      </div>
    </div>
  );
}