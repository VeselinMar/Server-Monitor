from sqlalchemy import Column, Integer, Float, String, DateTime
from core.database import Base


class ConnectivityCheck(Base):
    """
    ORM model representing a single connectivity check result.

    Maps to the 'connectivity_checks' table. Each row captures the outcome
    of a ping to 8.8.8.8, recorded every 20 minutes by connectivity_check.sh.
    """

    __tablename__ = "connectivity_checks"

    id = Column(Integer, primary_key=True, index=True)
    """Auto-incrementing primary key."""

    timestamp = Column(DateTime, index=True, nullable=False)
    """Date and time the check was recorded. Indexed for time-ordered queries."""

    status = Column(String, nullable=False)
    """Result of the check — either 'ONLINE' or 'NO INTERNET'."""

    latency_ms = Column(Float, nullable=True)
    """Round-trip latency in milliseconds. Null when status is NO INTERNET."""