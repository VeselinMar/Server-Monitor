from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class SpeedTestBase(BaseModel):
    """Shared fields present on all speed test records regardless of outcome."""

    timestamp: datetime
    """Date and time the speed test was recorded."""

    status: str
    """Raw status string from the CSV log, e.g. 'ONLINE' or 'FAILED'."""

    server_name: Optional[str]
    """Human-readable name of the speed test server used."""

    server_id: Optional[int]
    """Numeric identifier of the speed test server."""

    distance: Optional[float]
    """Distance to the speed test server, in kilometres."""

    model_config = ConfigDict(from_attributes=True)


class SpeedTestResultResponse(SpeedTestBase):
    """Response schema for a successful speed test result."""

    ping: float
    """Latency in milliseconds."""

    download_mbps: float
    """Download speed in megabits per second."""

    upload_mbps: float
    """Upload speed in megabits per second."""


class SpeedTestFailureResponse(SpeedTestBase):
    """Response schema for a failed speed test record."""

    failure_reason: str
    """Description of why the test was classified as a failure."""