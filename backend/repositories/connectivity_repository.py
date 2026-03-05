from sqlalchemy.orm import Session
from models.connectivity import ConnectivityCheck


def get_latest(db: Session):
    """
    Return the most recent connectivity check record.

    Returns None if no records exist.
    """
    return (
        db.query(ConnectivityCheck)
        .order_by(ConnectivityCheck.timestamp.desc())
        .first()
    )


def get_latest_timestamp(db: Session):
    """
    Return the most recent timestamp stored in the connectivity_checks table.

    Used by the ingest service to determine the cutoff point beyond which
    new rows should be inserted. Returns None if the table is empty.
    """
    return (
        db.query(ConnectivityCheck.timestamp)
        .order_by(ConnectivityCheck.timestamp.desc())
        .limit(1)
        .scalar()
    )


def get_counts(db: Session) -> dict:
    """
    Return record counts broken down by outcome.

    Returns a dict with three keys:
        - online: rows with status ONLINE
        - offline: rows with status NO INTERNET
        - total: sum of both
    """
    online = db.query(ConnectivityCheck).filter(ConnectivityCheck.status == "ONLINE").count()
    offline = db.query(ConnectivityCheck).filter(ConnectivityCheck.status == "NO INTERNET").count()

    return {
        "online": online,
        "offline": offline,
        "total": online + offline,
    }