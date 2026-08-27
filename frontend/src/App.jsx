import { useEffect, useState } from "react";
import NetworkMonitorPage from "./pages/NetworkMonitorPage";
import ServerHealthPage from "./pages/ServerHealthPage";
import SettingsModal from "./components/SettingsModal";

function getCurrentPage() {
  return window.location.pathname.startsWith(
    "/servermonitor/server-health",
  )
    ? "server-health"
    : "network";
}

export default function App() {
  const [page, setPage] = useState(getCurrentPage);
  const [showSettings, setShowSettings] = useState(false);

  function navigateTo(nextPage) {
    const path =
      nextPage === "server-health"
        ? "/servermonitor/server-health"
        : "/servermonitor/";

    window.history.pushState({}, "", path);
    setPage(nextPage);
  }

  useEffect(() => {
    const handlePopState = () => {
      setPage(getCurrentPage());
    };

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  return (
    <>
      <header className="header">
        <div className="header-left">
          <div className="header-dot" />

          <h1 className="header-title">
            ServerMonitor
          </h1>

          <span className="header-sub">
            {page === "server-health"
              ? "Server Health"
              : "Network Health Dashboard"}
          </span>
        </div>

        <div className="header-right">
          <nav className="header-nav">
            <button
              className={`header-nav-btn ${
                page === "network" ? "active" : ""
              }`}
              onClick={() => navigateTo("network")}
            >
              Network Monitor
            </button>

            <button
              className={`header-nav-btn ${
                page === "server-health" ? "active" : ""
              }`}
              onClick={() => navigateTo("server-health")}
            >
              Server Health
            </button>
          </nav>

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
        <SettingsModal
          onClose={() => setShowSettings(false)}
        />
      )}

      {page === "server-health" ? (
        <ServerHealthPage />
      ) : (
        <NetworkMonitorPage />
      )}
    </>
  );
}
