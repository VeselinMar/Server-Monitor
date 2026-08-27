from datetime import datetime

from sqlalchemy.orm import Session

from models.server_health_filesystem import ServerHealthFilesystem
from services.filesystem_health_service import apply_status
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
    health = (
        db.query(ServerHealth)
        .order_by(ServerHealth.timestamp.desc())
        .first()
    )

    if health is None:
        return None

    health.filesystems = (
        db.query(ServerHealthFilesystem)
        .filter(
            ServerHealthFilesystem.server_health_id == health.id
        )
        .order_by(ServerHealthFilesystem.mountpoint.asc())
        .all()
    )
    for filesystem in health.filesystems:
        apply_status(filesystem)


    return health



def get_history(
    db: Session,
    from_dt: datetime,
    to_dt: datetime,
) -> list[ServerHealth]:
    """
    Return server health samples within the specified time range,
    ordered chronologically.
    """
    health_samples = (
        db.query(ServerHealth)
        .filter(ServerHealth.timestamp >= from_dt)
        .filter(ServerHealth.timestamp <= to_dt)
        .order_by(ServerHealth.timestamp.asc())
        .all()
    )

    if not health_samples:
        return []

    health_ids = [health.id for health in health_samples]

    filesystems = (
        db.query(ServerHealthFilesystem)
        .filter(
            ServerHealthFilesystem.server_health_id.in_(health_ids)
        )
        .order_by(
            ServerHealthFilesystem.server_health_id.asc(),
            ServerHealthFilesystem.mountpoint.asc(),
        )
        .all()
    )

    filesystems_by_health_id: dict[int, list] = {}

    for filesystem in filesystems:
        filesystems_by_health_id.setdefault(
            filesystem.server_health_id,
            [],
        ).append(filesystem)

    for health in health_samples:
        health.filesystems = filesystems_by_health_id.get(
            health.id,
            [],
        )
    
        for filesystem in health.filesystems:
            apply_status(filesystem)

    return health_samples
