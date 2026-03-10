from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from core.database import SessionLocal
from models.speedtest import SpeedTestResult, SpeedTestFailure
from models.connectivity import ConnectivityCheck

router = APIRouter(prefix="/status", tags=["Status"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    summary="Get the timestamp of the most recent ingest across all data sources",
    response_description="Latest timestamp across speedtest results, failures, and connectivity checks",
)
def status(db: Session = Depends(get_db)):
    """
    Return the most recent record timestamp across all three tables.

    Used by the frontend to determine whether an automatic ingest is needed
    on page load — if the latest record is older than 20 minutes, ingest
    is triggered automatically.

    Returns null if no records exist yet.
    """
    timestamps = []

    t = db.query(SpeedTestResult.timestamp).order_by(SpeedTestResult.timestamp.desc()).limit(1).scalar()
    if t:
        timestamps.append(t)

    t = db.query(SpeedTestFailure.timestamp).order_by(SpeedTestFailure.timestamp.desc()).limit(1).scalar()
    if t:
        timestamps.append(t)

    t = db.query(ConnectivityCheck.timestamp).order_by(ConnectivityCheck.timestamp.desc()).limit(1).scalar()
    if t:
        timestamps.append(t)

    latest = max(timestamps) if timestamps else None

    return {"last_ingest": latest.isoformat() if latest else None}