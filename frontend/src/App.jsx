import { useState, useEffect, useCallback } from "react";
import { speedtest, connectivity } from "./api/client";
import SettingsModal from "./components/SettingsModal";
import { presetRange, toISO } from "./utils/dates";
import StatCard from "./components/StatCard";
import TimeRangeSelector from "./components/TimeRangeSelector";
import SpeedChart from "./components/SpeedChart";
import PingChart from "./components/PingChart";
import UptimeChart from "./components/UptimeChart";
import IncidentTable from "./components/IncidentTable";
import SummarySection from "./components/SummarySection";

const DEFAULT_PRESET = 24;

export default function App() {
  const [preset, setPreset] = useState(DEFAULT_PRESET);
  // For presets, only store hours and recompute "to" as now at fetch time.
  // For custom ranges, store explicit from/to dates.
  const [customFrom, setCustomFrom] = useState(null);
  const [customTo, setCustomTo] = useState(null);

  const [speedHistory, setSpeedHistory] = useState({ results: [], failures: [] });
  const [connHistory, setConnHistory] = useState([]);
  const [speedCounts, setSpeedCounts] = useState({ successful: 0, failed: 0, total: 0 });
  const [connCounts, setConnCounts] = useState({ online: 0, offline: 0, total: 0 });
  const [latest, setLatest] = useState(null);
  const [incidents, setIncidents] = useState([]);

  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [lastIngested, setLastIngested] = useState(null);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // Derive effective range at render time so presets always use "now"
  const effectiveRange = customFrom && customTo
    ? { from: customFrom, to: customTo }
    : presetRange(preset || DEFAULT_PRESET);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const range = customFrom && customTo
        ? { from: customFrom, to: customTo }
        : presetRange(preset || DEFAULT_PRESET);
      const fromISO = toISO(range.from);
      const toISO_ = toISO(range.to);
      const [sh, ch, sc, cc, lat, inc] = await Promise.all([
        speedtest.history(fromISO, toISO_),
        connectivity.history(fromISO, toISO_),
        speedtest.count(),
        connectivity.count(),
        speedtest.latest(),
        speedtest.incidents(fromISO, toISO_),
      ]);
      setSpeedHistory(sh);
      setConnHistory(ch);
      setSpeedCounts(sc);
      setConnCounts(cc);
      setLatest(lat);
      setIncidents(inc);
    } catch (e) {
      setError("Failed to fetch data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [preset, customFrom, customTo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  function handlePreset(hours) {
    setPreset(hours);
    setCustomFrom(null);
    setCustomTo(null);
  }

  function handleFrom(date) {
    setPreset(null);
    setCustomFrom(date);
  }

  function handleTo(date) {
    setPreset(null);
    setCustomTo(date);
  }

  async function handleIngest() {
    setIngesting(true);
    try {
      await Promise.all([speedtest.ingest(), connectivity.ingest()]);
      setLastIngested(new Date().toLocaleTimeString());
      await fetchData();
    } catch (e) {
      setError("Ingest failed. Check the backend logs.");
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="header-dot" />
          <h1 className="header-title">ServerMonitor</h1>
          <span className="header-sub">Network Health Dashboard</span>
        </div>
        <div className="header-right">
          {lastIngested && <span className="last-ingested">Last ingested {lastIngested}</span>}
          <button
            className={`ingest-btn ${ingesting ? "loading" : ""}`}
            onClick={handleIngest}
            disabled={ingesting}
          >
            {ingesting ? "Ingesting…" : "Ingest Logs"}
          </button>
          <button
            className="gear-btn"
            onClick={() => setShowSettings(true)}
            title="Settings"
          >
            ⚙
          </button>
        </div>
      </header>

      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}

      {error && <div className="error-banner">{error}</div>}

      <main className="main">
        <section className="stat-row">
          <StatCard
            label="Download"
            value={latest?.download_mbps?.toFixed(1)}
            unit=" Mbps"
            sub="Latest test"
            accent="#2563eb"
          />
          <StatCard
            label="Upload"
            value={latest?.upload_mbps?.toFixed(1)}
            unit=" Mbps"
            sub="Latest test"
            accent="#16a34a"
          />
          <StatCard
            label="Ping"
            value={latest?.ping?.toFixed(1)}
            unit=" ms"
            sub="Latest test"
            accent="#7c3aed"
          />
          <StatCard
            label="Connectivity"
            value={
              connCounts.total > 0
                ? ((connCounts.online / connCounts.total) * 100).toFixed(1)
                : null
            }
            unit="%"
            sub="Uptime all time"
            accent="#db2777"
          />
          <StatCard
            label="Speedtest"
            value={
              speedCounts.total > 0
                ? ((speedCounts.successful / speedCounts.total) * 100).toFixed(1)
                : null
            }
            unit="%"
            sub="Success rate all time"
            accent="#f59e0b"
          />
        </section>

        <TimeRangeSelector
          preset={preset}
          from={effectiveRange.from}
          to={effectiveRange.to}
          onPreset={handlePreset}
          onFrom={handleFrom}
          onTo={handleTo}
        />

        {loading ? (
          <div className="loading-state">Loading data…</div>
        ) : (
          <>
            <SpeedChart results={speedHistory.results} failures={speedHistory.failures} />
            <PingChart
              speedResults={speedHistory.results}
              connectivityChecks={connHistory}
            />
            <UptimeChart
              speedCounts={{
                successful: speedHistory.results.length,
                failed: speedHistory.failures.length,
              }}
              connCounts={{
                online: connHistory.filter((c) => c.status === "ONLINE").length,
                offline: connHistory.filter((c) => c.status === "NO INTERNET").length,
              }}
            />
            <IncidentTable incidents={incidents} />
            <div className="summary-divider" />
            <SummarySection />
          </>
        )}
      </main>
    </div>
  );
}