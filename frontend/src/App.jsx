import { useState, useEffect, useCallback } from "react";
import {
  speedtest,
  connectivity,
  status,
  serverHealth,
} from "./api/client";
import ServerHealthCards from "./components/ServerHealthCards";
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
const INGEST_THRESHOLD_MINUTES = 20;

const sortByTime = (arr) => [...arr].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

export default function App() {
  const [preset, setPreset] = useState(DEFAULT_PRESET);
  const [customFrom, setCustomFrom] = useState(null);
  const [customTo, setCustomTo] = useState(null);

  const [speedHistory, setSpeedHistory] = useState({ results: [], failures: [] });
  const [connHistory, setConnHistory] = useState([]);
  const [speedCounts, setSpeedCounts] = useState({ successful: 0, failed: 0, total: 0 });
  const [connCounts, setConnCounts] = useState({ online: 0, offline: 0, total: 0 });
  const [latest, setLatest] = useState(null);
  const [serverHealthLatest, setServerHealthLatest] = useState(null);
  const [incidents, setIncidents] = useState([]);

  const [loading, setLoading] = useState(false);
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

      let health = null;

      try {
        health = await serverHealth.latest();
      } catch {
        // Server health is optional; keep the network dashboard working.
      }
      setSpeedHistory({ results: sortByTime(sh.results), failures: sortByTime(sh.failures) });
      setConnHistory(sortByTime(ch));
      setSpeedCounts(sc);
      setConnCounts(cc);
      setLatest(lat);
      setServerHealthLatest(health);
      setIncidents(inc);
    } catch (e) {
      setError("Failed to fetch data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [preset, customFrom, customTo]);

  // On mount: check last ingest timestamp, trigger ingest if stale, then fetch
  useEffect(() => {
    async function initData() {
      try {
        const { last_ingest } = await status.get();
        const isStale = !last_ingest ||
          (Date.now() - new Date(last_ingest).getTime()) > INGEST_THRESHOLD_MINUTES * 60 * 1000;

        if (isStale) {
          await Promise.all([speedtest.ingest(), connectivity.ingest()]);
        }
      } catch {
        // Ingest failure is non-fatal — proceed to fetch whatever is in the DB
      }
      await fetchData();
    }
    initData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-fetch when time range changes (but skip the ingest check)
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

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="header-dot" />
          <h1 className="header-title">ServerMonitor</h1>
          <span className="header-sub">Network Health Dashboard</span>
        </div>
        <div className="header-right">
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
        <ServerHealthCards health={serverHealthLatest} />

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