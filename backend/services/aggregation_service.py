from datetime import date, datetime, timedelta
from itertools import groupby
from sqlalchemy.orm import Session

from models.speedtest import SpeedTestResult, SpeedTestFailure
from models.connectivity import ConnectivityCheck
from models.daily_summary import DailySummary


AGGREGATION_CUTOFF_DAYS = 7


def _average(values: list) -> float | None:
    """Return the average of a list of floats, or None if the list is empty."""
    return round(sum(values) / len(values), 2) if values else None


def _estimate_minutes(records: list, interval_minutes: int) -> int:
    """
    Estimate total minutes for a set of records based on their sampling interval.
    Each record represents one interval period.
    """
    return len(records) * interval_minutes


def _count_outages(checks: list) -> tuple[int, int]:
    """
    Count distinct outage events and total outage minutes from connectivity checks.

    An outage is a consecutive sequence of NO INTERNET checks. Each check
    represents a 20-minute interval.

    Returns (outage_count, outage_total_minutes).
    """
    outage_count = 0
    outage_minutes = 0
    in_outage = False

    for check in sorted(checks, key=lambda c: c.timestamp):
        if check.status == "NO INTERNET":
            if not in_outage:
                outage_count += 1
                in_outage = True
            outage_minutes += 20
        else:
            in_outage = False

    return outage_count, outage_minutes


def _count_degraded(results: list) -> tuple[int, int]:
    """
    Count degraded/critical tests and total degraded minutes.

    Each speedtest represents approximately a 60-minute interval under
    normal scheduling, or 10 minutes during adaptive testing. We use
    60 minutes as a conservative estimate.

    Returns (degraded_count, degraded_total_minutes).
    """
    degraded = [r for r in results if r.performance_status in ("DEGRADED", "CRITICAL")]
    return len(degraded), _estimate_minutes(degraded, 60)


def aggregate_old_records(db: Session) -> None:
    """
    Aggregate raw speedtest and connectivity records older than 7 days into
    daily summaries, then delete the raw records.

    For each calendar day older than the cutoff:
        1. Collect all SpeedTestResult, SpeedTestFailure, and ConnectivityCheck records
        2. Compute averages, minimums, counts, and incident metrics
        3. Upsert a DailySummary record (insert or update if already exists)
        4. Delete the raw records for that day

    This function is idempotent — re-running it on already-aggregated days
    is safe since the raw records will have been deleted.
    """
    cutoff_date = (datetime.now() - timedelta(days=AGGREGATION_CUTOFF_DAYS)).date()
    cutoff = datetime.combine(cutoff_date, time.min)

    # Fetch all raw records older than the cutoff
    old_results = (
        db.query(SpeedTestResult)
        .filter(SpeedTestResult.timestamp < cutoff)
        .order_by(SpeedTestResult.timestamp.asc())
        .all()
    )
    old_failures = (
        db.query(SpeedTestFailure)
        .filter(SpeedTestFailure.timestamp < cutoff)
        .order_by(SpeedTestFailure.timestamp.asc())
        .all()
    )
    old_checks = (
        db.query(ConnectivityCheck)
        .filter(ConnectivityCheck.timestamp < cutoff)
        .order_by(ConnectivityCheck.timestamp.asc())
        .all()
    )

    if not old_results and not old_failures and not old_checks:
        return

    # Group by calendar day
    def by_date(record):
        return record.timestamp.date()

    results_by_day = {
        d: list(g) for d, g in groupby(old_results, key=by_date)
    }
    failures_by_day = {
        d: list(g) for d, g in groupby(old_failures, key=by_date)
    }
    checks_by_day = {
        d: list(g) for d, g in groupby(old_checks, key=by_date)
    }

    all_days = set(results_by_day) | set(failures_by_day) | set(checks_by_day)

    for day in sorted(all_days):
        results = results_by_day.get(day, [])
        failures = failures_by_day.get(day, [])
        checks = checks_by_day.get(day, [])

        summary = db.query(DailySummary).filter(DailySummary.period_date == day).first()
        if summary is None:
            summary = DailySummary(period_date=day)
            db.add(summary)

        # Only update speedtest metrics if we have results to aggregate
        if results or failures:
            downloads = [r.download_mbps for r in results]
            uploads = [r.upload_mbps for r in results]
            pings = [r.ping for r in results if r.ping is not None]
            degraded_count, degraded_minutes = _count_degraded(results)

            summary.avg_download_mbps = _average(downloads)
            summary.min_download_mbps = min(downloads) if downloads else None
            summary.avg_upload_mbps = _average(uploads)
            summary.min_upload_mbps = min(uploads) if uploads else None
            summary.avg_ping = _average(pings)
            summary.total_tests = len(results) + len(failures)
            summary.successful_tests = len(results)
            summary.failed_tests = len(failures)
            summary.degraded_count = degraded_count
            summary.degraded_total_minutes = degraded_minutes

        # Only update connectivity metrics if we have checks to aggregate
        if checks:
            outage_count, outage_minutes = _count_outages(checks)
            summary.total_checks = len(checks)
            summary.online_checks = sum(1 for c in checks if c.status == "ONLINE")
            summary.offline_checks = sum(1 for c in checks if c.status == "NO INTERNET")
            summary.outage_count = outage_count
            summary.outage_total_minutes = outage_minutes

    db.commit()

    # Delete raw records now that they are summarised
    for r in old_results:
        db.delete(r)
    for f in old_failures:
        db.delete(f)
    for c in old_checks:
        db.delete(c)

    db.commit()