"""
Tests for /network/speedtest and /network/connectivity API endpoints.
"""

import pytest
from datetime import datetime
from conftest import (
    make_speedtest_result, make_speedtest_failure,
    make_connectivity_check,
)

# Wide date range used wherever endpoints require from_dt / to_dt
FROM = "2000-01-01T00:00:00"
TO   = "2099-12-31T23:59:59"


# ── Speedtest endpoints ────────────────────────────────────────────────────────

class TestSpeedtestLatest:

    def test_returns_none_on_empty_db(self, client):
        response = client.get("/network/speedtest/latest")
        assert response.status_code == 200
        assert response.json() is None

    def test_returns_most_recent_result(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0), download_mbps=100.0)
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 11, 0), download_mbps=120.0)
        data = client.get("/network/speedtest/latest").json()
        assert data["download_mbps"] == pytest.approx(120.0)

    def test_returns_failure_if_most_recent(self, client, db):
        make_speedtest_result(db,  timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_failure(db, timestamp=datetime(2026, 2, 1, 12, 0))
        data = client.get("/network/speedtest/latest").json()
        assert data["status"] == "FAILED"


class TestSpeedtestCount:

    def test_zeros_on_empty_db(self, client):
        data = client.get("/network/speedtest/count").json()
        assert data == {"successful": 0, "failed": 0, "total": 0}

    def test_counts_results_and_failures_separately(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 14, 0))
        make_speedtest_failure(db, timestamp=datetime(2026, 2, 1, 13, 0))
        data = client.get("/network/speedtest/count").json()
        assert data["successful"] == 2
        assert data["failed"] == 1
        assert data["total"] == 3


class TestSpeedtestHistory:

    def test_returns_all_results_when_wide_range(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_result(db, timestamp=datetime(2026, 2, 2, 10, 0))
        data = client.get("/network/speedtest/history", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data["results"]) == 2

    def test_filters_by_from_dt(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_result(db, timestamp=datetime(2026, 2, 5, 10, 0))
        data = client.get(
            "/network/speedtest/history",
            params={"from_dt": "2026-02-03T00:00:00", "to_dt": TO},
        ).json()
        results = data["results"]
        assert len(results) == 1
        assert results[0]["timestamp"].startswith("2026-02-05")

    def test_filters_by_to_dt(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_result(db, timestamp=datetime(2026, 2, 5, 10, 0))
        data = client.get(
            "/network/speedtest/history",
            params={"from_dt": FROM, "to_dt": "2026-02-03T00:00:00"},
        ).json()
        results = data["results"]
        assert len(results) == 1
        assert results[0]["timestamp"].startswith("2026-02-01")

    def test_returns_empty_list_outside_range(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0))
        data = client.get(
            "/network/speedtest/history",
            params={"from_dt": "2026-03-01T00:00:00", "to_dt": TO},
        ).json()
        assert data["results"] == []
        assert data["failures"] == []

    def test_missing_params_returns_422(self, client):
        response = client.get("/network/speedtest/history")
        assert response.status_code == 422


class TestSpeedtestIncidents:

    def test_no_incidents_when_all_normal(self, client, db):
        for hour in range(5):
            make_speedtest_result(
                db,
                timestamp=datetime(2026, 2, 1, hour, 0),
                performance_status="NORMAL",
            )
        data = client.get("/network/speedtest/incidents", params={"from_dt": FROM, "to_dt": TO}).json()
        assert data == []

    def test_single_degraded_block_is_one_incident(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0), performance_status="NORMAL")
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 11, 0), performance_status="DEGRADED")
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 12, 0), performance_status="DEGRADED")
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 13, 0), performance_status="NORMAL")
        data = client.get("/network/speedtest/incidents", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data) == 1
        assert data[0]["type"] == "DEGRADED"
        assert data[0]["sample_count"] == 2

    def test_adjacent_critical_and_degraded_are_separate_incidents(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0), performance_status="CRITICAL")
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 11, 0), performance_status="DEGRADED")
        data = client.get("/network/speedtest/incidents", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data) == 2

    def test_failures_are_included_in_incidents(self, client, db):
        make_speedtest_failure(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_speedtest_failure(db, timestamp=datetime(2026, 2, 1, 11, 0))
        data = client.get("/network/speedtest/incidents", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data) == 1
        assert data[0]["type"] == "FAILURE"
        assert data[0]["sample_count"] == 2

    def test_incident_has_required_fields(self, client, db):
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 10, 0), performance_status="CRITICAL")
        data = client.get("/network/speedtest/incidents", params={"from_dt": FROM, "to_dt": TO}).json()
        incident = data[0]
        for field in ["type", "start", "end", "duration_minutes", "sample_count"]:
            assert field in incident

    def test_missing_params_returns_422(self, client):
        response = client.get("/network/speedtest/incidents")
        assert response.status_code == 422


# ── Connectivity endpoints ─────────────────────────────────────────────────────

class TestConnectivityLatest:

    def test_returns_none_on_empty_db(self, client):
        response = client.get("/network/connectivity/latest")
        assert response.status_code == 200
        assert response.json() is None

    def test_returns_most_recent_check(self, client, db):
        make_connectivity_check(db, timestamp=datetime(2026, 2, 1, 10, 0), latency_ms=10.0)
        make_connectivity_check(db, timestamp=datetime(2026, 2, 1, 11, 0), latency_ms=20.0)
        data = client.get("/network/connectivity/latest").json()
        assert data["latency_ms"] == pytest.approx(20.0)


class TestConnectivityCount:

    def test_zeros_on_empty_db(self, client):
        data = client.get("/network/connectivity/count").json()
        assert data["total"] == 0

    def test_counts_online_and_offline(self, client, db):
        make_connectivity_check(db, status="ONLINE",      timestamp=datetime(2026, 2, 1, 10, 0))
        make_connectivity_check(db, status="NO INTERNET", timestamp=datetime(2026, 2, 1, 10, 20))
        make_connectivity_check(db, status="ONLINE",      timestamp=datetime(2026, 2, 1, 10, 40))
        data = client.get("/network/connectivity/count").json()
        assert data["total"] == 3


class TestConnectivityHistory:

    def test_returns_all_when_wide_range(self, client, db):
        make_connectivity_check(db, timestamp=datetime(2026, 2, 1, 10, 0))
        make_connectivity_check(db, timestamp=datetime(2026, 2, 2, 10, 0))
        data = client.get("/network/connectivity/history", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data) == 2

    def test_offline_events_included(self, client, db):
        make_connectivity_check(db, status="NO INTERNET", timestamp=datetime(2026, 2, 1, 10, 0), latency_ms=None)
        data = client.get("/network/connectivity/history", params={"from_dt": FROM, "to_dt": TO}).json()
        assert len(data) == 1
        assert data[0]["status"] == "NO INTERNET"

    def test_missing_params_returns_422(self, client):
        response = client.get("/network/connectivity/history")
        assert response.status_code == 422