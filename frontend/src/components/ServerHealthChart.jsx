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

import { parseUTCTimestamp } from "../utils/dates";

const formatTime = (value) =>
  parseUTCTimestamp(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

const formatPercent = (value) =>
  value == null ? "—" : `${value.toFixed(1)}%`;

const formatTemp = (value) =>
  value == null ? "—" : `${value.toFixed(0)}°C`;

export default function ServerHealthChart({ history }) {
  if (!history?.length) {
    return (
      <section className="chart-section server-health-chart-section">
        <div className="section-heading">
          <div>
            <h2>Server Health History</h2>
            <p>No server health history available for this period</p>
          </div>
        </div>
      </section>
    );
  }

  const data = [...history]
    .sort(
      (a, b) =>
        parseUTCTimestamp(a.timestamp) -
        parseUTCTimestamp(b.timestamp)
    )
    .map((item) => ({
      ...item,
      memory_percent:
        item.memory_total_bytes
          ? (item.memory_used_bytes / item.memory_total_bytes) * 100
          : null,
      disk_percent:
        item.filesystems?.find(
          (fs) => fs.mountpoint === "/"
        )?.percent ?? null,
    }));

  return (
    <section className="chart-section server-health-chart-section">
      <div className="section-heading">
        <div>
          <h2>Server Health History</h2>
          <p>CPU, memory, disk, temperature and load</p>
        </div>
      </div>

      <div className="server-health-chart">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e5e7eb"
            />

            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTime}
              stroke="#6b7280"
              fontSize={12}
            />

            <YAxis
              yAxisId="percent"
              domain={[0, 100]}
              stroke="#6b7280"
              fontSize={12}
            />

            <YAxis
              yAxisId="temp"
              orientation="right"
              stroke="#ef4444"
              fontSize={12}
            />

            <Tooltip
              labelFormatter={(value) =>
                parseUTCTimestamp(value).toLocaleString()
              }
              formatter={(value, name) => {
                if (name === "Temperature") {
                  return [formatTemp(value), name];
                }

                if (
                  name === "CPU" ||
                  name === "Memory" ||
                  name === "Disk"
                ) {
                  return [formatPercent(value), name];
                }

                return [value?.toFixed?.(2) ?? value, name];
              }}
            />

            <Legend />

            <Line
              yAxisId="percent"
              type="monotone"
              dataKey="cpu_percent"
              name="CPU"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              connectNulls
            />

            <Line
              yAxisId="percent"
              type="monotone"
              dataKey="memory_percent"
              name="Memory"
              stroke="#7c3aed"
              strokeWidth={2}
              dot={false}
              connectNulls
            />

            <Line
              yAxisId="percent"
              type="monotone"
              dataKey="disk_percent"
              name="Disk"
              stroke="#db2777"
              strokeWidth={2}
              dot={false}
              connectNulls
            />

            <Line
              yAxisId="temp"
              type="monotone"
              dataKey="cpu_package_temp_c"
              name="Temperature"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
