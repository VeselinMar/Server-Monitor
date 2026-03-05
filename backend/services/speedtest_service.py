from sqlalchemy.orm import Session
from repositories import speedtest_repository as repo


def get_latest(db: Session):
    """
    Return the most recent speed test record across both results and failures.

    Delegates to the speedtest repository.
    """
    return repo.get_latest(db)


def get_counts(db: Session) -> dict:
    """
    Return record counts broken down by outcome.

    Delegates to the speedtest repository. Returns counts for successful,
    failed, and total records.
    """
    return repo.get_counts(db)

def get_latest_timestamp(db: Session):
    """
    Return the most recent timestamp stored across both results and failures.

    Delegates to the speedtest repository.
    """
    return repo.get_latest_timestamp(db)