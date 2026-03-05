from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime
from typing import Optional


class ConnectivityCheckResponse(BaseModel):
    """Response schema for a connectivity check record."""

    timestamp: datetime
    """Date and time the check was recorded."""

    status: str
    """Result of the check — either 'ONLINE' or 'NO INTERNET'."""

    latency_ms: Optional[float]
    """Round-trip latency in milliseconds. Null when status is NO INTERNET."""

    model_config = ConfigDict(from_attributes=True)