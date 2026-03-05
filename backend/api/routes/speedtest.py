from typing import Union
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from schemas.speedtest import SpeedTestResultResponse, SpeedTestFailureResponse
from core.database import SessionLocal
from services.ingest_speedtest import ingest_speedtest
from services.speedtest_service import get_latest, get_counts, get_latest_timestamp, get_history

router = APIRouter(prefix="/speedtest", tags=["Speedtest"])


def get_db():
    """
    Dependency that provides a database session.

    Yields a SQLAlchemy session and ensures it is closed after the request
    completes, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/latest",
    summary="Get the latest speed test record regardless of outcome",
    response_description="The most recent speed test record across both results and failures",
    response_model=Union[SpeedTestResultResponse, SpeedTestFailureResponse],
)
def latest(db: Session = Depends(get_db)):
    """
    Retrieve the most recent speed test record across both tables.

    Delegates to the speedtest repository. Returns `null` if neither table
    contains any records.
    """
    return get_latest(db)


@router.get(
    "/count",
    summary="Get record counts broken down by outcome",
    response_description="Count of successful results, failures, and total combined",
)
def count(db: Session = Depends(get_db)):
    """
    Return record counts broken down by outcome.

    Delegates to the speedtest repository. Returns counts for successful,
    failed, and total records.
    """
    return get_counts(db)


@router.post(
    "/ingest",
    summary="Ingest speed test results from the CSV log",
    response_description="A status message confirming the speed test data was ingested",
)
def ingest():
    """
    Parse the speed test CSV log and persist records to the database.

    Reads from the configured log file, coerces numeric fields, and routes
    each row to either SpeedTestResult or SpeedTestFailure. Returns a
    confirmation status on success.
    """
    ingest_speedtest()
    return {"status": "ingested"}

@router.get(
    "/history",
    summary="Get speed test records within a time range",
    response_description="All speed test results and failures within the given time range",
)
def history(
    from_dt: datetime,
    to_dt: datetime,
    db: Session = Depends(get_db),
):
    """
    Return all speed test records between from_dt and to_dt.

    Both parameters are required and should be ISO 8601 timestamps.
    Returns results and failures separately so the frontend can
    distinguish successful tests from failed ones on the same timeline.
    """
    return get_history(db, from_dt, to_dt)    