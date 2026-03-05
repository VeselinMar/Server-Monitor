from sqlalchemy.orm import Session
from models.speedtest import SpeedTestResult, SpeedTestFailure


def get_latest(db: Session):
    """
    Return the most recent speed test record across both results and failures.

    Queries SpeedTestResult and SpeedTestFailure independently, then returns
    whichever has the more recent timestamp. Returns None if both tables are empty.
    """
    latest_result = (
        db.query(SpeedTestResult)
        .order_by(SpeedTestResult.timestamp.desc())
        .first()
    )
    latest_failure = (
        db.query(SpeedTestFailure)
        .order_by(SpeedTestFailure.timestamp.desc())
        .first()
    )

    if latest_result is None:
        return latest_failure
    if latest_failure is None:
        return latest_result

    return latest_result if latest_result.timestamp >= latest_failure.timestamp else latest_failure

def get_counts(db: Session) -> dict:
    """
    Return record counts broken down by outcome.

    Returns a dict with three keys:
        - successful: rows in SpeedTestResult
        - failed: rows in SpeedTestFailure
        - total: sum of both
    """
    successful = db.query(SpeedTestResult).count()
    failed = db.query(SpeedTestFailure).count()

    return {
        "successful": successful,
        "failed": failed,
        "total": successful + failed,
    }

def get_latest_timestamp(db: Session):
    """
    Return the most recent timestamp stored across both results and failures.

    Used by the ingest service to determine the cutoff point beyond which
    new rows should be inserted. Returns None if both tables are empty.
    """
    latest_result = (
        db.query(SpeedTestResult.timestamp)
        .order_by(SpeedTestResult.timestamp.desc())
        .limit(1)
        .scalar()
    )
    latest_failure = (
        db.query(SpeedTestFailure.timestamp)
        .order_by(SpeedTestFailure.timestamp.desc())
        .limit(1)
        .scalar()
    )

    if latest_result is None:
        return latest_failure
    if latest_failure is None:
        return latest_result

    return max(latest_result, latest_failure)