import { useState, useEffect } from "react";
import { summary } from "../api/client";
import { subDays, format } from "date-fns";
import SummaryChart from "./SummaryChart";
import SummaryStats from "./SummaryStats";

const RANGES = [
  { label: "Last 30 days", days: 30 },
  { label: "All time",     days: null },
];

const API_BASE = "http://localhost:8000";

export default function SummarySection() {
  const [activeRange, setActiveRange] = useState(0);
  const [summaries, setSummaries]     = useState([]);
  const [loading, setLoading]         = useState(false);
  const [fromDate, setFromDate]       = useState("");
  const [toDate, setToDate]           = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const to   = format(new Date(), "yyyy-MM-dd");
        const from = RANGES[activeRange].days
          ? format(subDays(new Date(), RANGES[activeRange].days), "yyyy-MM-dd")
          : "2000-01-01";
        setFromDate(from);
        setToDate(to);
        const data = await summary.history(from, to);
        setSummaries(data);
      } catch (e) {
        setSummaries([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [activeRange]);

  const reportUrl = fromDate && toDate
    ? `${API_BASE}/network/report/pdf?from_date=${fromDate}&to_date=${toDate}`
    : null;

  return (
    <section className="summary-section">
      <div className="summary-header">
        <h2 className="summary-title">Historical Data</h2>
        <div className="summary-header-actions">
          <div className="preset-buttons">
            {RANGES.map((r, i) => (
              <button
                key={r.label}
                className={`preset-btn ${activeRange === i ? "active" : ""}`}
                onClick={() => setActiveRange(i)}
              >
                {r.label}
              </button>
            ))}
          </div>
          {reportUrl && (
            <a
              href={reportUrl}
              download
              className="export-btn"
            >
              Export PDF Report
            </a>
          )}
        </div>
      </div>
      {loading ? (
        <div className="loading-state">Loading historical data…</div>
      ) : (
        <>
          <SummaryStats summaries={summaries} />
          <SummaryChart summaries={summaries} />
        </>
      )}
    </section>
  );
}