from sqlalchemy.orm import Session
from repositories import connectivity_repository as repo


def get_latest(db: Session):
    """
    Return the most recent connectivity check record.

    Delegates to the connectivity repository.
    """
    return repo.get_latest(db)


def get_latest_timestamp(db: Session):
    """
    Return the most recent timestamp stored in the connectivity_checks table.

    Delegates to the connectivity repository.
    """
    return repo.get_latest_timestamp(db)


def get_counts(db: Session) -> dict:
    """
    Return record counts broken down by outcome.

    Delegates to the connectivity repository.
    """
    return repo.get_counts(db)