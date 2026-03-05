import math
import pandas as pd
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.speedtest import SpeedTestResult, SpeedTestFailure
from services.speedtest_service import get_latest_timestamp
from pathlib import Path

LOG_PATH = Path("/mnt/media/monitoring/data/speedtest.csv")

DOWNLOAD_DEGRADED = 75.0   # Drei guaranteed minimum (50% of 150 Mbps)
DOWNLOAD_CRITICAL = 30.0
UPLOAD_DEGRADED = 5.0
UPLOAD_CRITICAL = 2.0

COLUMNS = [
    "timestamp",
    "status",
    "ping",
    "download_mbps",
    "upload_mbps",
    "server_name",
    "server_id",
    "distance",
    "failure_reason",
]

NUMERIC_COLS = ["ping", "download_mbps", "upload_mbps", "server_id", "distance"]

def classify_speed(download_mbps: float, upload_mbps: float) -> str:
    """
    Classify a speed test result based on Drei MyLife FIX Data 150 thresholds.

    Returns 'CRITICAL' if either metric is severely below contracted levels,
    'DEGRADED' if below the guaranteed minimum, or 'NORMAL' otherwise.
    """
    if download_mbps < DOWNLOAD_CRITICAL or upload_mbps < UPLOAD_CRITICAL:
        return "CRITICAL"
    elif download_mbps < DOWNLOAD_DEGRADED or upload_mbps < UPLOAD_DEGRADED:
        return "DEGRADED"
    return "NORMAL"

def _columns_for(model) -> set:
    """Return the set of column names defined on a SQLAlchemy model."""
    return set(model.__table__.columns.keys())


def _sanitise(data: dict) -> dict:
    """Replace float NaN values with None for SQLAlchemy compatibility."""
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in data.items()
    }

def ingest_speedtest():
    """
    Read the speed test CSV log and insert only records newer than the latest
    stored timestamp.

    Successful runs (status == 'ONLINE', all core metrics present) are written
    to SpeedTestResult. All other rows are written to SpeedTestFailure,
    preserving the full test history for accurate uptime and reliability analysis.

    Skips any rows whose timestamp is less than or equal to the most recent
    timestamp already present in the database, preventing duplicate entries
    on repeated ingest calls.

    CSV format (headerless, 8 columns on success, 9 on failure):
        timestamp, status, ping, download_mbps, upload_mbps,
        server_name, server_id, distance[, failure_reason]

    Failure reasons:
        - Taken directly from the CSV's 9th column when present.
        - 'missing_metrics' if status is ONLINE but core metrics could not be parsed.

    Raises:
        FileNotFoundError: If LOG_PATH does not exist.
        sqlalchemy.exc.SQLAlchemyError: If the database commit fails.
    """
    df = pd.read_csv(
        LOG_PATH,
        header=None,
        names=COLUMNS,
        parse_dates=["timestamp"],
        on_bad_lines="skip",
        engine="python",
    )

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    db: Session = SessionLocal()

    try:
        latest_timestamp = get_latest_timestamp(db)

        if latest_timestamp is not None:
            df = df[df["timestamp"] > pd.Timestamp(latest_timestamp)]

        if df.empty:
            return

        for _, row in df.iterrows():
            data = _sanitise(row.to_dict())

            if row["status"] != "ONLINE":
                failure_reason = data.get("failure_reason") or f"status:{row['status']}"
                db.add(SpeedTestFailure(
                    **{k: v for k, v in data.items() if k in _columns_for(SpeedTestFailure) and k != "failure_reason"},
                    failure_reason=failure_reason,
                ))
            elif pd.isna(row[["ping", "download_mbps", "upload_mbps"]]).any():
                db.add(SpeedTestFailure(
                    **{k: v for k, v in data.items() if k in _columns_for(SpeedTestFailure) and k != "failure_reason"},
                    failure_reason="missing_metrics",
                ))
            else:
                db.add(SpeedTestResult(
                **{k: v for k, v in data.items() if k in _columns_for(SpeedTestResult)},
                performance_status=classify_speed(row["download_mbps"], row["upload_mbps"]),
            ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()  