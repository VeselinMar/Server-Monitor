import { useCallback, useEffect, useState } from "react";
import { serverHealth } from "../api/client";
import ServerHealthCards from "../components/ServerHealthCards";
import ServerHealthChart from "../components/ServerHealthChart";
import { presetRange, toISO } from "../utils/dates";

const DEFAULT_PRESET = 24;

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

export default function ServerHealthPage() {
  const [preset, setPreset] = useState(DEFAULT_PRESET);
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const range = presetRange(preset);

      const [latestData, historyData] = await Promise.all([
        serverHealth.latest(),
        serverHealth.history(
          toISO(range.from),
          toISO(range.to),
        ),
      ]);

      setLatest(latestData);
      setHistory(
        Array.isArray(historyData)
          ? historyData
          : historyData?.results ?? [],
      );
    } catch {
      setError("Failed to fetch server health data.");
    } finally {
      setLoading(false);
    }
  }, [preset]);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  const filesystems = latest?.filesystems ?? [];

  return (
    <main className="main server-health-page">
      <div className="server-health-page-header">
        <div>
          <div className="page-eyebrow">SYSTEM MONITORING</div>
          <h1>Server Health</h1>
          <p>
            CPU, memory, storage and system performance.
          </p>
        </div>

        <button
          className="refresh-btn"
          onClick={loadHealth}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <ServerHealthCards health={latest} />

      <section className="health-history-panel">
        <div className="section-heading">
          <div>
            <h2>Performance History</h2>
            <p>Resource utilization over time.</p>
          </div>

          <div className="preset-buttons">
            {[1, 6, 24, 72].map((hours) => (
              <button
                key={hours}
                className={`preset-btn ${
                  preset === hours ? "active" : ""
                }`}
                onClick={() => setPreset(hours)}
              >
                {hours < 24 ? `${hours}h` : `${hours / 24}d`}
              </button>
            ))}
          </div>
        </div>

        <ServerHealthChart history={history} />
      </section>

      <section className="filesystem-panel">
        <div className="section-heading">
          <div>
            <h2>Filesystems</h2>
            <p>Storage usage reported by the server.</p>
          </div>
        </div>

        <div className="filesystem-list">
          {filesystems.length === 0 ? (
            <div className="empty-state">
              No filesystem data available.
            </div>
          ) : (
            filesystems.map((filesystem) => (
              <div
                className="filesystem-row"
                key={filesystem.mountpoint}
              >
                <div className="filesystem-info">
                  <strong>{filesystem.mountpoint}</strong>

                  {filesystem.device && (
                    <span>{filesystem.device}</span>
                  )}
                </div>

                <div className="filesystem-usage">
                  <div className="filesystem-bar">
                    <div
                      className="filesystem-bar-fill"
                      style={{
                        width: `${Math.min(
                          filesystem.percent ?? 0,
                          100,
                        )}%`,
                      }}
                    />
                  </div>

                  <strong>
                    {filesystem.percent != null
                      ? `${filesystem.percent.toFixed(1)}%`
                      : "—"}
                  </strong>

                  <span>
                    {formatBytes(filesystem.used_bytes)} /{" "}
                    {formatBytes(filesystem.total_bytes)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
