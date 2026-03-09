"""
Tests for the PDF report generation service and /network/report/pdf endpoint.

Covers:
- generate_report returns bytes
- Output is valid PDF (correct magic bytes)
- Report uses subscriber details from settings, not hardcoded values
- Report uses dynamic threshold from settings
- Endpoint returns 200 with PDF content-type
- Endpoint returns PDF even with no data (empty summaries/incidents)
- Contractual basis paragraph reflects configured thresholds
"""

import pytest
from datetime import date
from unittest.mock import MagicMock

from services.report_service import generate_report
import io
try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

def _pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return " ".join(page.extract_text() or "" for page in reader.pages)
from conftest import make_daily_summary, make_setting


def _mock_summary(**kwargs):
    """Create a mock DailySummary object with sensible defaults."""
    defaults = dict(
        period_date          = date(2026, 2, 1),
        avg_download_mbps    = 110.0,
        min_download_mbps    = 80.0,
        avg_upload_mbps      = 9.0,
        avg_ping             = 14.0,
        successful_tests     = 8,
        failed_tests         = 0,
        total_tests          = 8,
        outage_count         = 0,
        outage_total_minutes = 0,
    )
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


DEFAULT_SETTINGS = {
    "subscriber_name":           "Veselin Todorov",
    "subscriber_address":        "Mariahilfer Strasse 1, Vienna",
    "subscriber_account_number": "DREI-12345678",
    "subscriber_email":          "test@example.com",
    "subscriber_phone":          "+43 123 456789",
    "subscriber_plan":           "MyLife FIX Data 150",
    "subscriber_provider":       "Drei Austria GmbH",
    "contracted_download_mbps":  "150.0",
    "contracted_upload_mbps":    "0.0",
    "download_degraded_mbps":    "75.0",
    "download_critical_mbps":    "30.0",
    "upload_degraded_mbps":      "5.0",
    "upload_critical_mbps":      "2.0",
}


class TestGenerateReport:

    def test_returns_bytes(self):
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], DEFAULT_SETTINGS
        )
        assert isinstance(pdf, bytes)

    def test_output_is_valid_pdf(self):
        """PDF files start with the %PDF magic bytes."""
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], DEFAULT_SETTINGS
        )
        assert pdf[:4] == b"%PDF"

    def test_nonempty_output(self):
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], DEFAULT_SETTINGS
        )
        assert len(pdf) > 1000   # even an empty report should be a real PDF

    def test_uses_subscriber_name_from_settings(self):
        settings = {**DEFAULT_SETTINGS, "subscriber_name": "Test Person"}
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], settings
        )
        assert "Test Person" in _pdf_text(pdf)

    def test_uses_provider_from_settings(self):
        settings = {**DEFAULT_SETTINGS, "subscriber_provider": "Test ISP GmbH"}
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], settings
        )
        assert "Test ISP GmbH" in _pdf_text(pdf)

    def test_uses_plan_from_settings(self):
        settings = {**DEFAULT_SETTINGS, "subscriber_plan": "Ultra Fast 500"}
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], settings
        )
        assert "Ultra Fast 500" in _pdf_text(pdf)

    def test_uses_download_guarantee_from_settings(self):
        """The contractual minimum in the report should reflect the configured threshold."""
        settings = {**DEFAULT_SETTINGS, "download_degraded_mbps": "100.0", "contracted_download_mbps": "200.0"}
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 28), [], [], settings
        )
        assert "100" in _pdf_text(pdf)

    def test_with_summaries_and_incidents(self):
        """Report should not raise when given real data."""
        summaries = [
            _mock_summary(period_date=date(2026, 2, 1), avg_download_mbps=60.0),
            _mock_summary(period_date=date(2026, 2, 2), avg_download_mbps=45.0),
        ]
        incidents = [
            {
                "type": "DEGRADED",
                "start": "2026-02-01 10:00:00",
                "end":   "2026-02-01 12:00:00",
                "duration_minutes": 120,
                "sample_count": 2,
                "avg_download_mbps": 55.0,
                "avg_upload_mbps": 3.0,
                "avg_ping": 20.0,
            }
        ]
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 2), summaries, incidents, DEFAULT_SETTINGS
        )
        assert pdf[:4] == b"%PDF"

    def test_below_guarantee_days_counted_correctly(self):
        """Days with avg_download below the threshold should be counted in findings."""
        summaries = [
            _mock_summary(period_date=date(2026, 2, 1), avg_download_mbps=60.0),  # below 75
            _mock_summary(period_date=date(2026, 2, 2), avg_download_mbps=90.0),  # above 75
        ]
        pdf = generate_report(
            date(2026, 2, 1), date(2026, 2, 2), summaries, [], DEFAULT_SETTINGS
        )
        assert "1 of 2" in _pdf_text(pdf)


class TestReportEndpoint:

    def test_pdf_endpoint_returns_200(self, client):
        response = client.get(
            "/network/report/pdf",
            params={"from_date": "2026-02-01", "to_date": "2026-02-28"},
        )
        assert response.status_code == 200

    def test_pdf_endpoint_returns_pdf_content_type(self, client):
        response = client.get(
            "/network/report/pdf",
            params={"from_date": "2026-02-01", "to_date": "2026-02-28"},
        )
        assert "application/pdf" in response.headers["content-type"]

    def test_pdf_endpoint_returns_valid_pdf_bytes(self, client):
        response = client.get(
            "/network/report/pdf",
            params={"from_date": "2026-02-01", "to_date": "2026-02-28"},
        )
        assert response.content[:4] == b"%PDF"

    def test_pdf_endpoint_includes_content_disposition(self, client):
        response = client.get(
            "/network/report/pdf",
            params={"from_date": "2026-02-01", "to_date": "2026-02-28"},
        )
        assert "attachment" in response.headers.get("content-disposition", "")
        assert ".pdf" in response.headers.get("content-disposition", "")

    def test_pdf_endpoint_with_data(self, client, db):
        make_daily_summary(db, period_date=date(2026, 2, 1), avg_download_mbps=60.0)
        make_setting(db, "subscriber_name", "Veselin Todorov")
        response = client.get(
            "/network/report/pdf",
            params={"from_date": "2026-02-01", "to_date": "2026-02-28"},
        )
        assert response.status_code == 200
        assert response.content[:4] == b"%PDF"

    def test_pdf_endpoint_missing_dates_returns_422(self, client):
        response = client.get("/network/report/pdf")
        assert response.status_code == 422