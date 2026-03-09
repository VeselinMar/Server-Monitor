import StatCard from "./StatCard";

function totalOutageHours(summaries) {
  const mins = summaries.reduce((s, d) => s + (d.outage_total_minutes || 0), 0);
  if (mins === 0) return "0 min";
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function worstDay(summaries) {
  if (!summaries.length) return null;
  const worst = summaries.reduce((a, b) =>
    (a.outage_total_minutes || 0) > (b.outage_total_minutes || 0) ? a : b
  );
  if (!worst.outage_total_minutes) return "None";
  return worst.period_date.slice(5); // MM-DD
}

function avgDownload(summaries) {
  const valid = summaries.filter((s) => s.avg_download_mbps != null);
  if (!valid.length) return null;
  return (valid.reduce((s, d) => s + d.avg_download_mbps, 0) / valid.length).toFixed(1);
}

function totalFailed(summaries) {
  return summaries.reduce((s, d) => s + (d.failed_tests || 0), 0);
}

function totalOutages(summaries) {
  return summaries.reduce((s, d) => s + (d.outage_count || 0), 0);
}

export default function SummaryStats({ summaries }) {
  if (!summaries || summaries.length === 0) return null;

  return (
    <div className="stat-row">
      <StatCard
        label="Total Outage Time"
        value={totalOutageHours(summaries)}
        sub={`${totalOutages(summaries)} distinct outage${totalOutages(summaries) !== 1 ? "s" : ""}`}
        accent="#ef4444"
      />
      <StatCard
        label="Worst Day"
        value={worstDay(summaries)}
        sub="Most outage time"
        accent="#f59e0b"
      />
      <StatCard
        label="Avg Download"
        value={avgDownload(summaries)}
        unit=" Mbps"
        sub="Historical average"
        accent="#2563eb"
      />
      <StatCard
        label="Failed Tests"
        value={totalFailed(summaries)}
        sub="Speedtest failures"
        accent="#7c3aed"
      />
      <StatCard
        label="Days Covered"
        value={summaries.length}
        sub="Aggregated days"
        accent="#db2777"
      />
    </div>
  );
}