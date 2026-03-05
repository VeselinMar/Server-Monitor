from typing import Union
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import SessionLocal
from schemas.connectivity import ConnectivityCheckResponse
from services.connectivity_service import get_latest, get_counts
from services.ingest_connectivity import ingest_connectivity

router = APIRouter(prefix="/connectivity", tags=["Connectivity"])


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
    summary="Get the latest connectivity check record",
    response_description="The most recent connectivity check record",
    response_model=ConnectivityCheckResponse,
)
def latest(db: Session = Depends(get_db)):
    """
    Retrieve the most recent connectivity check record.

    Delegates to the connectivity service. Returns `null` if no records exist.
    """
    return get_latest(db)


@router.get(
    "/count",
    summary="Get connectivity check counts broken down by outcome",
    response_description="Count of online, offline, and total connectivity checks",
)
def count(db: Session = Depends(get_db)):
    """
    Return record counts broken down by outcome.

    Delegates to the connectivity service. Returns counts for online,
    offline, and total records.
    """
    return get_counts(db)


@router.post(
    "/ingest",
    summary="Ingest connectivity check results from the CSV log",
    response_description="A status message confirming the connectivity data was ingested",
)
def ingest():
    """
    Parse the connectivity check CSV log and persist new records to the database.

    Reads from the configured log file, coerces numeric fields, and inserts
    all rows newer than the latest stored timestamp. Returns a confirmation
    status on success.
    """
    ingest_connectivity()
    return {"status": "ingested"}