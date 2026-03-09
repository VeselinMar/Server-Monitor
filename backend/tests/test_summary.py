"""
Tests for /network/summary endpoints and the aggregation service.

Covers:
- GET /network/summary/latest returns None on empty DB
- GET /network/summary/history respects date range filters
- Aggregation creates DailySummary rows from raw data
- Aggregation upsert is idempotent (safe to run multiple times)
- Aggregation only covers days older than the cutoff
- Aggregation skips days with no data
"""

import pytest
from datetime import datetime, date, timedelta
from conftest import (
    make_speedtest_result, make_speedtest_failure,
    make_connectivity_check, make_daily_summary,
)


# ── Summary endpoints ──────────────────────────────────────────────────────────

class TestSummaryLatest:

    def test_returns_none_on_empty_db(self, client):
        response = client.get("/network/summary/latest")
        assert response.status_code == 200
        assert response.json() is None

    def test_returns_most_recent_summary(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1), avg_download_mbps=80.0)
        make_daily_summary(db, period_date=date(2026, 1, 2), avg_download_mbps=95.0)
        data = client.get("/network/summary/latest").json()
        assert data["avg_download_mbps"] == pytest.approx(95.0)
        assert data["period_date"] == "2026-01-02"


class TestSummaryHistory:

    def test_returns_all_when_no_filter(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1))
        make_daily_summary(db, period_date=date(2026, 1, 2))
        data = client.get("/network/summary/history", params={"from_date": "2000-01-01", "to_date": "2099-12-31"}).json()
        assert len(data) == 2

    def test_filters_by_from_date(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1))
        make_daily_summary(db, period_date=date(2026, 1, 10))
        data = client.get(
            "/network/summary/history",
            params={"from_date": "2026-01-05", "to_date": "2099-12-31"},
        ).json()
        assert len(data) == 1
        assert data[0]["period_date"] == "2026-01-10"

    def test_filters_by_to_date(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1))
        make_daily_summary(db, period_date=date(2026, 1, 10))
        data = client.get(
            "/network/summary/history",
            params={"from_date": "2000-01-01", "to_date": "2026-01-05"},
        ).json()
        assert len(data) == 1
        assert data[0]["period_date"] == "2026-01-01"

    def test_returns_empty_list_outside_range(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1))
        data = client.get(
            "/network/summary/history",
            params={"from_date": "2026-03-01", "to_date": "2099-12-31"},
        ).json()
        assert data == []

    def test_summary_has_required_fields(self, client, db):
        make_daily_summary(db, period_date=date(2026, 1, 1))
        data = client.get("/network/summary/history", params={"from_date": "2000-01-01", "to_date": "2099-12-31"}).json()
        row = data[0]
        for field in [
            "period_date", "avg_download_mbps", "min_download_mbps",
            "avg_upload_mbps", "avg_ping", "successful_tests",
            "failed_tests", "total_tests", "outage_count",
        ]:
            assert field in row


# ── Aggregation service ────────────────────────────────────────────────────────

class TestAggregationService:

    def _cutoff_date(self):
        """Aggregation only covers days older than 7 days."""
        from services.aggregation_service import AGGREGATION_CUTOFF_DAYS
        return date.today() - timedelta(days=AGGREGATION_CUTOFF_DAYS + 1)

    def test_creates_daily_summary_from_speedtest_results(self, db):
        from services.aggregation_service import aggregate_old_records as aggregate
        from models.daily_summary import DailySummary

        old_date = self._cutoff_date()
        make_speedtest_result(db, timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0), download_mbps=100.0, upload_mbps=8.0, ping=12.0, performance_status="NORMAL")
        make_speedtest_result(db, timestamp=datetime(old_date.year, old_date.month, old_date.day, 11, 0), download_mbps=80.0,  upload_mbps=6.0, ping=15.0, performance_status="NORMAL")

        aggregate(db)

        summaries = db.query(DailySummary).all()
        assert len(summaries) == 1
        assert summaries[0].period_date == old_date
        assert summaries[0].successful_tests == 2
        assert summaries[0].avg_download_mbps == pytest.approx(90.0)

    def test_aggregation_is_idempotent(self, db):
        from services.aggregation_service import aggregate_old_records as aggregate
        from models.daily_summary import DailySummary

        old_date = self._cutoff_date()
        make_speedtest_result(db, timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0), performance_status="NORMAL")

        aggregate(db)
        aggregate(db)  # run twice

        assert db.query(DailySummary).count() == 1

    def test_aggregation_skips_recent_data(self, db):
        """Data within the cutoff window must not be aggregated."""
        from services.aggregation_service import aggregate_old_records as aggregate
        from models.daily_summary import DailySummary

        # Use yesterday — inside the 7-day window
        yesterday = date.today() - timedelta(days=1)
        make_speedtest_result(db, timestamp=datetime(yesterday.year, yesterday.month, yesterday.day, 10, 0), performance_status="NORMAL")

        aggregate(db)

        assert db.query(DailySummary).count() == 0

    def test_aggregation_counts_failures(self, db):
        from services.aggregation_service import aggregate_old_records as aggregate
        from models.daily_summary import DailySummary

        old_date = self._cutoff_date()
        make_speedtest_result(db, timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0), performance_status="NORMAL")
        make_speedtest_failure(db, timestamp=datetime(old_date.year, old_date.month, old_date.day, 11, 0))

        aggregate(db)

        summary = db.query(DailySummary).first()
        assert summary.failed_tests == 1
        assert summary.total_tests == 2

    def test_aggregation_computes_outage_minutes(self, db):
        from services.aggregation_service import aggregate_old_records as aggregate
        from models.daily_summary import DailySummary

        old_date = self._cutoff_date()
        # Two NO INTERNET checks 20 minutes apart = ~20 min outage
        make_connectivity_check(db, status="NO INTERNET", timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0),  latency_ms=None)
        make_connectivity_check(db, status="NO INTERNET", timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 20), latency_ms=None)
        make_connectivity_check(db, status="ONLINE",      timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 40), latency_ms=10.0)

        aggregate(db)

        summary = db.query(DailySummary).first()
        assert summary.outage_count >= 1
        assert summary.outage_total_minutes > 0

    def test_aggregate_endpoint_returns_200(self, client):
        response = client.post("/network/summary/aggregate")
        assert response.status_code == 200

    def test_aggregation_completes_and_creates_summary(self, db):
        """
        Call aggregate_old_records directly (not as a background task) and
        verify it actually creates a DailySummary row — tests the task body,
        not just the HTTP trigger.
        """
        from services.aggregation_service import aggregate_old_records
        from models.daily_summary import DailySummary

        old_date = self._cutoff_date()
        make_speedtest_result(
            db,
            timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0),
            performance_status="NORMAL",
        )
        make_connectivity_check(
            db,
            timestamp=datetime(old_date.year, old_date.month, old_date.day, 10, 0),
            status="ONLINE",
        )

        aggregate_old_records(db)

        summary = db.query(DailySummary).filter(DailySummary.period_date == old_date).first()
        assert summary is not None
        assert summary.successful_tests == 1
        assert summary.total_checks == 1