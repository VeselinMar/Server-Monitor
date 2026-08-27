const formatBytes = (bytes) => {
  if (bytes == null) return "—";

  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;

  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }

  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
};

const formatUptime = (seconds) => {
  if (seconds == null) return "—";

  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const percentage = (used, total) => {
  if (!total) return null;
  return (used / total) * 100;
};

function HealthCard({ label, value, unit, sub, accent }) {
  return (
    <div className="health-card" style={{ "--health-accent": accent }}>
      <div className="health-card-label">{label}</div>

      <div className="health-card-value">
        {value ?? "—"}
        {value != null && unit && (
          <span className="health-card-unit">{unit}</span>
        )}
      </div>

      <div className="health-card-sub">{sub}</div>
    </div>
  );
}

export default function ServerHealthCards({ health }) {
  if (!health) {
    return (
      <section className="server-health-section">
        <div className="section-heading">
          <div>
            <h2>Server Health</h2>
            <p>No server health data available</p>
          </div>
        </div>
      </section>
    );
  }

  const memoryPercent = percentage(
    health.memory_used_bytes,
    health.memory_total_bytes,
  );

  const filesystem = health.filesystems ?? [];

  const rootFilesystem = filesystem.find(
    (fs) => fs.mountpoint === "/",
  );

  return (
    <section className="server-health-section">
      <div className="section-heading">
        <div>
          <h2>Server Health</h2>
          <p>
            Last updated{" "}
            {health.timestamp
              ? new Date(health.timestamp).toLocaleString()
              : "—"}
          </p>
        </div>
      </div>

      <div className="health-card-grid">
        <HealthCard
          label="CPU"
          value={health.cpu_percent?.toFixed(1)}
          unit="%"
          sub={
            health.cpu_package_temp_c != null
              ? `${health.cpu_package_temp_c.toFixed(0)}°C`
              : "Temperature unavailable"
          }
          accent="#2563eb"
        />

        <HealthCard
          label="Memory"
          value={memoryPercent?.toFixed(1)}
          unit="%"
          sub={
            memoryPercent != null
              ? `${formatBytes(health.memory_used_bytes)} / ${formatBytes(
                  health.memory_total_bytes,
                )}`
              : "Memory data unavailable"
          }
          accent="#7c3aed"
        />

        <HealthCard
          label="Load"
          value={health.load_1?.toFixed(2)}
          unit=""
          sub={
            health.load_5 != null && health.load_15 != null
              ? `5m ${health.load_5.toFixed(2)} · 15m ${health.load_15.toFixed(2)}`
              : "Load data unavailable"
          }
          accent="#f59e0b"
        />

        <HealthCard
          label="Uptime"
          value={formatUptime(health.uptime_seconds)}
          unit=""
          sub="System uptime"
          accent="#16a34a"
        />

        <HealthCard
          label="Disk"
          value={rootFilesystem?.percent?.toFixed(1)}
          unit="%"
          sub={
            rootFilesystem
              ? `${formatBytes(rootFilesystem.used_bytes)} / ${formatBytes(
                  rootFilesystem.total_bytes,
                )}`
              : "Filesystem data unavailable"
          }
          accent="#db2777"
        />
      </div>
    </section>
  );
}
