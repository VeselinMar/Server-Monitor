"""
Tests for speedtest and connectivity ingestion services, plus
performance classification logic.

Covers:
- classify_speed threshold boundaries (NORMAL / DEGRADED / CRITICAL)
- classify_speed uses thresholds from settings, not hardcoded values
- ingest_speedtest deduplication, routing, classification, empty CSV
- ingest_connectivity deduplication, routing, empty CSV
- reclassify_all updates existing rows when thresholds change
"""

import csv
import os
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch

from services.ingest_speedtest import classify_speed, ingest_speedtest, reclassify_all
from conftest import make_setting, make_speedtest_result


# ── classify_speed ─────────────────────────────────────────────────────────────

DEFAULT_THRESHOLDS = {
    "download_degraded": 75.0,
    "download_critical": 30.0,
    "upload_degraded":   5.0,
    "upload_critical":   2.0,
}


class TestClassifySpeed:

    def test_normal_above_all_thresholds(self):
        assert classify_speed(120.0, 10.0, DEFAULT_THRESHOLDS) == "NORMAL"

    def test_normal_exactly_at_degraded_boundary(self):
        assert classify_speed(75.0, 5.0, DEFAULT_THRESHOLDS) == "NORMAL"

    def test_degraded_download_just_below_threshold(self):
        assert classify_speed(74.9, 10.0, DEFAULT_THRESHOLDS) == "DEGRADED"

    def test_degraded_upload_just_below_threshold(self):
        assert classify_speed(120.0, 4.9, DEFAULT_THRESHOLDS) == "DEGRADED"

    def test_critical_download_below_critical_threshold(self):
        assert classify_speed(29.9, 10.0, DEFAULT_THRESHOLDS) == "CRITICAL"

    def test_critical_upload_below_critical_threshold(self):
        assert classify_speed(120.0, 1.9, DEFAULT_THRESHOLDS) == "CRITICAL"

    def test_critical_both_metrics_bad(self):
        assert classify_speed(10.0, 0.5, DEFAULT_THRESHOLDS) == "CRITICAL"

    def test_critical_takes_priority_over_degraded(self):
        assert classify_speed(25.0, 10.0, DEFAULT_THRESHOLDS) == "CRITICAL"

    def test_degraded_exactly_at_critical_boundary(self):
        assert classify_speed(30.0, 5.0, DEFAULT_THRESHOLDS) == "DEGRADED"

    def test_custom_thresholds_respected(self):
        custom = {
            "download_degraded": 100.0,
            "download_critical": 50.0,
            "upload_degraded":   20.0,
            "upload_critical":   10.0,
        }
        assert classify_speed(80.0, 25.0, custom) == "DEGRADED"

    def test_zero_speeds_are_critical(self):
        assert classify_speed(0.0, 0.0, DEFAULT_THRESHOLDS) == "CRITICAL"


# ── CSV helpers ────────────────────────────────────────────────────────────────

def _write_speedtest_csv(path, rows):
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


def _write_connectivity_csv(path, rows):
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


def _tmp_csv(rows, writer_fn):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    path = f.name
    f.close()
    writer_fn(path, rows)
    return path


NORMAL_ROW = ["2026-02-01 10:00:00", "ONLINE", "15.0", "120.0", "10.0", "Vienna", "1234", "5.0", ""]
DEGRADED_ROW = ["2026-02-01 11:00:00", "ONLINE", "20.0", "60.0", "4.0", "Vienna", "1234", "5.0", ""]
CRITICAL_ROW = ["2026-02-01 12:00:00", "ONLINE", "30.0", "20.0", "1.0", "Vienna", "1234", "5.0", ""]
FAILURE_ROW  = ["2026-02-01 13:00:00", "FAILED", "", "", "", "", "", "", "Connection timeout"]

ONLINE_CHECK  = ["2026-02-01 10:00:00", "ONLINE", "12.0"]
OFFLINE_CHECK = ["2026-02-01 10:20:00", "NO INTERNET", ""]


# ── ingest_speedtest ───────────────────────────────────────────────────────────

class TestIngestSpeedtest:

    def test_successful_row_stored_as_result(self, db):
        from models.speedtest import SpeedTestResult, SpeedTestFailure
        path = _tmp_csv([NORMAL_ROW], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
            assert db.query(SpeedTestResult).count() == 1
            assert db.query(SpeedTestFailure).count() == 0
        finally:
            os.unlink(path)

    def test_failed_row_stored_as_failure(self, db):
        from models.speedtest import SpeedTestResult, SpeedTestFailure
        path = _tmp_csv([FAILURE_ROW], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
            assert db.query(SpeedTestFailure).count() == 1
            assert db.query(SpeedTestResult).count() == 0
        finally:
            os.unlink(path)

    def test_mixed_rows_split_correctly(self, db):
        from models.speedtest import SpeedTestResult, SpeedTestFailure
        path = _tmp_csv([NORMAL_ROW, FAILURE_ROW, CRITICAL_ROW], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
            assert db.query(SpeedTestResult).count() == 2
            assert db.query(SpeedTestFailure).count() == 1
        finally:
            os.unlink(path)

    def test_deduplication_on_reingest(self, db):
        from models.speedtest import SpeedTestResult
        path = _tmp_csv([NORMAL_ROW], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
                ingest_speedtest(db)
            assert db.query(SpeedTestResult).count() == 1
        finally:
            os.unlink(path)

    def test_classification_stored_correctly(self, db):
        from models.speedtest import SpeedTestResult
        path = _tmp_csv([NORMAL_ROW, DEGRADED_ROW, CRITICAL_ROW], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
            statuses = {r.performance_status for r in db.query(SpeedTestResult).all()}
            assert statuses == {"NORMAL", "DEGRADED", "CRITICAL"}
        finally:
            os.unlink(path)

    def test_custom_thresholds_from_settings(self, db):
        from models.speedtest import SpeedTestResult
        make_setting(db, "download_degraded_mbps", "130.0")
        make_setting(db, "download_critical_mbps", "30.0")
        make_setting(db, "upload_degraded_mbps",   "5.0")
        make_setting(db, "upload_critical_mbps",   "2.0")
        make_setting(db, "contracted_download_mbps", "150.0")
        make_setting(db, "contracted_upload_mbps",   "0.0")
        path = _tmp_csv([NORMAL_ROW], _write_speedtest_csv)  # 120 Mbps — below 130
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
            result = db.query(SpeedTestResult).first()
            assert result.performance_status == "DEGRADED"
        finally:
            os.unlink(path)

    def test_empty_csv_does_not_raise(self, db):
        path = _tmp_csv([], _write_speedtest_csv)
        try:
            with patch("services.ingest_speedtest.LOG_PATH", path):
                ingest_speedtest(db)
        finally:
            os.unlink(path)


# ── reclassify_all ─────────────────────────────────────────────────────────────

class TestReclassifyAll:

    def test_updates_rows_when_threshold_changes(self, db):
        from models.speedtest import SpeedTestResult
        # Insert a row classified as NORMAL at default thresholds
        make_speedtest_result(db, download_mbps=80.0, upload_mbps=6.0, performance_status="NORMAL")
        # Now raise the degraded threshold above 80 Mbps
        make_setting(db, "download_degraded_mbps", "100.0")
        make_setting(db, "download_critical_mbps", "30.0")
        make_setting(db, "upload_degraded_mbps",   "5.0")
        make_setting(db, "upload_critical_mbps",   "2.0")
        make_setting(db, "contracted_download_mbps", "150.0")
        make_setting(db, "contracted_upload_mbps",   "0.0")

        updated = reclassify_all(db)

        assert updated == 1
        result = db.query(SpeedTestResult).first()
        assert result.performance_status == "DEGRADED"

    def test_returns_zero_when_nothing_changes(self, db):
        make_speedtest_result(db, download_mbps=120.0, upload_mbps=10.0, performance_status="NORMAL")
        updated = reclassify_all(db)
        assert updated == 0

    def test_does_not_touch_already_correct_rows(self, db):
        from models.speedtest import SpeedTestResult
        make_speedtest_result(db, download_mbps=120.0, upload_mbps=10.0, performance_status="NORMAL")
        make_speedtest_result(db, timestamp=datetime(2026, 2, 1, 14, 0), download_mbps=60.0, upload_mbps=4.0, performance_status="DEGRADED")
        updated = reclassify_all(db)
        assert updated == 0


# ── ingest_connectivity ────────────────────────────────────────────────────────

class TestIngestConnectivity:

    def _ingest(self, db, path):
        from services.ingest_connectivity import ingest_connectivity
        with patch("services.ingest_connectivity.LOG_PATH", path):
            ingest_connectivity(db)

    def test_online_check_stored(self, db):
        from models.connectivity import ConnectivityCheck
        path = _tmp_csv([ONLINE_CHECK], _write_connectivity_csv)
        try:
            self._ingest(db, path)
            assert db.query(ConnectivityCheck).count() == 1
            assert db.query(ConnectivityCheck).first().status == "ONLINE"
        finally:
            os.unlink(path)

    def test_offline_check_stored(self, db):
        from models.connectivity import ConnectivityCheck
        path = _tmp_csv([OFFLINE_CHECK], _write_connectivity_csv)
        try:
            self._ingest(db, path)
            check = db.query(ConnectivityCheck).first()
            assert check.status == "NO INTERNET"
            assert check.latency_ms is None
        finally:
            os.unlink(path)

    def test_deduplication_on_reingest(self, db):
        from models.connectivity import ConnectivityCheck
        path = _tmp_csv([ONLINE_CHECK], _write_connectivity_csv)
        try:
            self._ingest(db, path)
            self._ingest(db, path)
            assert db.query(ConnectivityCheck).count() == 1
        finally:
            os.unlink(path)

    def test_mixed_checks_stored_correctly(self, db):
        from models.connectivity import ConnectivityCheck
        path = _tmp_csv([ONLINE_CHECK, OFFLINE_CHECK], _write_connectivity_csv)
        try:
            self._ingest(db, path)
            assert db.query(ConnectivityCheck).count() == 2
        finally:
            os.unlink(path)

    def test_empty_csv_does_not_raise(self, db):
        path = _tmp_csv([], _write_connectivity_csv)
        try:
            self._ingest(db, path)
        finally:
            os.unlink(path)