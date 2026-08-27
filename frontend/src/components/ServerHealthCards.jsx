const formatBytes = (bytes) => {
  if (bytes == null) return "—";

  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;

  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
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

function HealthCard({
  label,
  value,
  unit,
  sub,
  accent,
  progress,
  detail,
  className = "",
  children,
}) {
  return (
    <article
      className={`health-card ${className}`}
      style={{ "--health-accent": accent }}
    >
      <div className="health-card-top">
        <div className="health-card-label">
          <span className="health-card-dot" />
          {label}
        </div>

        {detail && (
          <span className="health-card-detail">{detail}</span>
        )}
      </div>

      <div className="health-card-value">
        {value ?? "—"}
        {value != null && unit && (
          <span className="health-card-unit">{unit}</span>
        )}
      </div>

      {children || (
        <>
          <div className="health-card-sub">{sub}</div>

          {progress != null && (
            <div className="health-card-progress">
              <div
                className="health-card-progress-fill"
                style={{
                  width: `${Math.min(Math.max(progress, 0), 100)}%`,
                }}
              />
            </div>
          )}
        </>
      )}
    </article>
  );
}

export default function ServerHealthCards({ health }) {
  if (!health) {
    return (
      <section className="server-health-section">
        <div className="health-empty-state">
          <span className="health-empty-dot" />

          <div>
            <h2>Server Health</h2>
            <p>No server health data available.</p>
          </div>
        </div>
      </section>
    );
  }

  const memoryPercent = percentage(
    health.memory_used_bytes,
    health.memory_total_bytes,
  );

  const filesystems = health.filesystems ?? [];

  const rootFilesystem = filesystems.find(
    (filesystem) => filesystem.mountpoint === "/",
  );

  return (
    <section className="server-health-section">
      <div className="health-section-meta">
        <div>
          <div className="health-section-label">SERVER HEALTH</div>

          <div className="health-section-status">
            <span className="health-status-dot" />
            System operating normally
          </div>
        </div>

        <div className="health-updated">
          <span>LAST UPDATED</span>
          <strong>
            {health.timestamp
              ? new Date(health.timestamp).toLocaleString()
              : "—"}
          </strong>
        </div>
      </div>

      <div className="health-card-grid">
        <HealthCard
          label="CPU"
          value={health.cpu_percent?.toFixed(1)}
          unit="%"
          sub={
            health.cpu_package_temp_c != null
              ? `${health.cpu_package_temp_c.toFixed(0)}°C package temperature`
              : "Temperature unavailable"
          }
          progress={health.cpu_percent}
          accent="#2563eb"
          detail="PROCESSOR"
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
          progress={memoryPercent}
          accent="#7c3aed"
          detail="RAM"
        />

        <HealthCard
          label="Load"
          value={health.load_1?.toFixed(2)}
          accent="#f59e0b"
          detail="SYSTEM"
          className="health-card-load"
        >
          <div className="load-metrics">
            <div>
              <span>1 MIN</span>
              <strong>{health.load_1?.toFixed(2) ?? "—"}</strong>
            </div>

            <div>
              <span>5 MIN</span>
              <strong>{health.load_5?.toFixed(2) ?? "—"}</strong>
            </div>

            <div>
              <span>15 MIN</span>
              <strong>{health.load_15?.toFixed(2) ?? "—"}</strong>
            </div>
          </div>
        </HealthCard>

        <HealthCard
          label="Uptime"
          value={formatUptime(health.uptime_seconds)}
          sub="System uptime"
          accent="#16a34a"
          detail="RUNTIME"
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
          progress={rootFilesystem?.percent}
          accent="#db2777"
          detail="/"
        />
      </div>
    </section>
  );
}
