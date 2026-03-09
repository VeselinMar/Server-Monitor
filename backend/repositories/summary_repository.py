from datetime import date
from sqlalchemy.orm import Session
from models.daily_summary import DailySummary


def get_summaries(db: Session, from_date: date, to_date: date) -> list:
    """
    Return all daily summaries within the given date range, ordered
    chronologically.
    """
    return (
        db.query(DailySummary)
        .filter(DailySummary.period_date >= from_date)
        .filter(DailySummary.period_date <= to_date)
        .order_by(DailySummary.period_date.asc())
        .all()
    )


def get_latest_summary(db: Session):
    """Return the most recent daily summary record."""
    return (
        db.query(DailySummary)
        .order_by(DailySummary.period_date.desc())
        .first()
    )