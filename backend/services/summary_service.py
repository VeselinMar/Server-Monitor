from datetime import date
from sqlalchemy.orm import Session
from repositories import summary_repository as repo


def get_summaries(db: Session, from_date: date, to_date: date) -> list:
    """
    Return all daily summaries within the given date range.

    Delegates to the summary repository.
    """
    return repo.get_summaries(db, from_date, to_date)


def get_latest_summary(db: Session):
    """
    Return the most recent daily summary.

    Delegates to the summary repository.
    """
    return repo.get_latest_summary(db)