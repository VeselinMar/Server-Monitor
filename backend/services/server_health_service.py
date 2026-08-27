from datetime import datetime

from sqlalchemy.orm import Session

from models.server_health import ServerHealth
from repositories import server_health_repository as repo


def create(db: Session, health: ServerHealth) -> ServerHealth:
    """
    Store a server health sample.
    """
    return repo.create(db, health)


def get_latest(db: Session) -> ServerHealth | None:
    """
    Return the most recent server health sample.
    """
    return repo.get_latest(db)


def get_history(
    db: Session,
    from_dt: datetime,
    to_dt: datetime,
) -> list[ServerHealth]:
    """
    Return server health samples within the specified time range,
    ordered chronologically.
    """
    return repo.get_history(db, from_dt, to_dt)
