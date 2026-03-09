from datetime import date
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import SessionLocal
from services.summary_service import get_summaries, get_latest_summary
from services.aggregation_service import aggregate_old_records

router = APIRouter(prefix="/summary", tags=["Summary"])


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
    "/history",
    summary="Get daily summaries within a date range",
    response_description="List of daily summary records ordered chronologically",
)
def history(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
):
    """
    Return all daily summaries between from_date and to_date.

    Dates should be in ISO 8601 format (YYYY-MM-DD).
    """
    return get_summaries(db, from_date, to_date)


@router.get(
    "/latest",
    summary="Get the most recent daily summary",
    response_description="The most recent daily summary record",
)
def latest(db: Session = Depends(get_db)):
    """
    Return the most recent daily summary record.

    Returns null if no summaries have been generated yet.
    """
    return get_latest_summary(db)


@router.post(
    "/aggregate",
    summary="Manually trigger aggregation of old records",
    response_description="Status message confirming aggregation ran",
)
def aggregate(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually trigger the aggregation job as a background task.

    Aggregation also runs automatically after every ingest call. This
    endpoint is useful for triggering an initial aggregation or for
    debugging.
    """
    background_tasks.add_task(aggregate_old_records, db)
    return {"status": "aggregation started"}