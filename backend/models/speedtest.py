from sqlalchemy import Column, Integer, Float, String, DateTime
from core.database import Base
import sqlalchemy as sa


class SpeedTestMixin:
    """
    Shared columns for all speed test records, regardless of outcome.

    Provides the common time/server context that is available for both
    successful and failed test runs.
    """

    id = Column(Integer, primary_key=True, index=True)
    """Auto-incrementing primary key."""

    timestamp = Column(DateTime, index=True, nullable=False)
    """Date and time the speed test was recorded. Indexed for time-ordered queries."""

    status = Column(String, nullable=False)
    """Raw status string from the CSV log, e.g. 'ONLINE' or 'FAILED'."""

    server_name = Column(String, nullable=True)
    """Human-readable name of the speed test server used."""

    server_id = Column(Integer, nullable=True)
    """Numeric identifier of the speed test server."""

    distance = Column(Float, nullable=True)
    """Distance to the speed test server, in kilometres."""


class SpeedTestResult(SpeedTestMixin, Base):
    """
    ORM model representing a successful speed test result.

    Maps to the 'speedtest_results' table. Only rows where the test completed
    successfully (status == 'ONLINE') and all performance metrics are present
    should be inserted here.
    """

    __tablename__ = "speedtest_results"

    ping = Column(Float, nullable=False)
    """Latency in milliseconds."""

    download_mbps = Column(Float, nullable=False)
    """Download speed in megabits per second."""

    upload_mbps = Column(Float, nullable=False)
    """Upload speed in megabits per second."""


class SpeedTestFailure(SpeedTestMixin, Base):
    """
    ORM model representing a failed or incomplete speed test.

    Maps to the 'speedtest_failures' table. Captures any run where the test
    did not complete successfully — either due to a non-ONLINE status or missing
    performance metrics. Preserving these records prevents uptime and reliability
    metrics from being positively skewed by silently discarding failures.
    """

    __tablename__ = "speedtest_failures"

    failure_reason = Column(String, nullable=False)

    """
    Short description of why the record was classified as a failure. Possible values:
        - 'status:<value>' — test reported a non-ONLINE status (e.g. 'status:FAILED')
        - 'missing_metrics' — status was ONLINE but one or more of ping,
          download_mbps, or upload_mbps could not be parsed
    """