from typing import Literal


HealthStatus = Literal["ok", "warning", "critical"]


WARNING_PERCENT = 80.0
CRITICAL_PERCENT = 90.0


def get_status(percent: float | None) -> HealthStatus:
    """
    Evaluate filesystem capacity or inode usage.
    """

    if percent is None:
        return "ok"

    if percent >= CRITICAL_PERCENT:
        return "critical"

    if percent >= WARNING_PERCENT:
        return "warning"

    return "ok"


def evaluate_filesystem(
    percent: float | None,
    inode_percent: float | None,
) -> dict[str, HealthStatus]:
    """
    Evaluate filesystem capacity and inode usage independently.
    """

    return {
        "capacity": get_status(percent),
        "inodes": get_status(inode_percent),
    }


def get_filesystem_status(
    percent: float | None,
    inode_percent: float | None,
) -> tuple[HealthStatus, HealthStatus]:
    result = evaluate_filesystem(
        percent,
        inode_percent,
    )

    return (
        result["capacity"],
        result["inodes"],
    )


def apply_status(filesystem) -> None:
    """
    Add derived health status values to a filesystem ORM object.

    These values are transient and are not stored in the database.
    """

    filesystem.capacity_status = get_status(
        filesystem.percent
    )

    filesystem.inode_status = get_status(
        filesystem.inode_percent
    )
