from datetime import datetime

from sqlalchemy.orm import Session

from models.server_health import ServerHealth


def create(db: Session, health: ServerHealth) -> ServerHealth:
    """
    Store a server health sample.
    """
    db.add(health)
    db.commit()
    db.refresh(health)
    return health


def get_latest(db: Session) -> ServerHealth | None:
    """
    Return the most recent server health sample.
    """
    return (
        db.query(ServerHealth)
        .order_by(ServerHealth.timestamp.desc())
        .first()
    )


def get_history(
    db: Session,
    from_dt: datetime,
    to_dt: datetime,
) -> list[ServerHealth]:
    """
    Return server health samples within the specified time range,
    ordered chronologically.
    """
    return (
        db.query(ServerHealth)
        .filter(ServerHealth.timestamp >= from_dt)
        .filter(ServerHealth.timestamp <= to_dt)
        .order_by(ServerHealth.timestamp.asc())
        .all()
    )
