from sqlalchemy import Column, Integer, Float, String, Date
from core.database import Base


class DailySummary(Base):
    """
    ORM model representing an aggregated daily summary of network health.

    Maps to the 'daily_summaries' table. Each row covers one calendar day
    and is generated automatically after ingest by the aggregation service
    once raw records are older than 7 days. The corresponding raw records
    are deleted after aggregation.

    Covers both speedtest and connectivity data for the day.
    """

    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, index=True)
    """Auto-incrementing primary key."""

    period_date = Column(Date, unique=True, index=True, nullable=False)
    """The calendar date this summary covers."""

    # ── Speedtest metrics ──
    avg_download_mbps = Column(Float)
    """Average download speed across all successful tests for the day."""

    min_download_mbps = Column(Float)
    """Lowest recorded download speed for the day."""

    avg_upload_mbps = Column(Float)
    """Average upload speed across all successful tests for the day."""

    min_upload_mbps = Column(Float)
    """Lowest recorded upload speed for the day."""

    avg_ping = Column(Float)
    """Average ping across all successful tests for the day."""

    total_tests = Column(Integer, default=0)
    """Total number of speedtest attempts for the day."""

    successful_tests = Column(Integer, default=0)
    """Number of speedtest attempts that completed successfully."""

    failed_tests = Column(Integer, default=0)
    """Number of speedtest attempts that failed."""

    degraded_count = Column(Integer, default=0)
    """Number of successful tests classified as DEGRADED or CRITICAL."""

    degraded_total_minutes = Column(Integer, default=0)
    """Estimated total minutes spent in a degraded state."""

    # ── Connectivity metrics ──
    total_checks = Column(Integer, default=0)
    """Total number of connectivity checks for the day."""

    online_checks = Column(Integer, default=0)
    """Number of connectivity checks with status ONLINE."""

    offline_checks = Column(Integer, default=0)
    """Number of connectivity checks with status NO INTERNET."""

    outage_count = Column(Integer, default=0)
    """Number of distinct outage events detected for the day."""

    outage_total_minutes = Column(Integer, default=0)
    """Estimated total minutes of connectivity outage for the day."""