"""
Speedtest CSV ingest service.

Reads the speedtest log CSV, deduplicates against the latest stored timestamp,
and routes each row to SpeedTestResult or SpeedTestFailure. Performance
classification thresholds are read from the settings table so they can be
updated via the UI without restarting the server.
"""

import os
import pandas as pd
from sqlalchemy.orm import Session
from pathlib import Path

from core.database import SessionLocal
from models.speedtest import SpeedTestResult, SpeedTestFailure
from repositories import settings_repository as settings_repo

Path(os.getenv("LOG_PATH_SPEEDTEST", "/mnt/media/monitoring/data/speedtest.csv"))


def _get_thresholds(db: Session) -> dict:
    """
    Read performance classification thresholds from the settings table.

    Falls back to defaults (Drei MyLife FIX Data 150) if not configured.
    """
    settings = settings_repo.get_all(db)
    return {
        "download_degraded": float(settings["download_degraded_mbps"]),
        "download_critical": float(settings["download_critical_mbps"]),
        "upload_degraded":   float(settings["upload_degraded_mbps"]),
        "upload_critical":   float(settings["upload_critical_mbps"]),
    }


def classify_speed(download_mbps: float, upload_mbps: float, thresholds: dict) -> str:
    """
    Classify a speed test result based on configured thresholds.

    Returns:
        'CRITICAL'  — either metric is severely below contracted levels
        'DEGRADED'  — either metric is below the guaranteed minimum
        'NORMAL'    — both metrics are above the guaranteed minimum
    """
    if download_mbps < thresholds["download_critical"] or upload_mbps < thresholds["upload_critical"]:
        return "CRITICAL"
    elif download_mbps < thresholds["download_degraded"] or upload_mbps < thresholds["upload_degraded"]:
        return "DEGRADED"
    return "NORMAL"


def _columns_for(model) -> set:
    """Return the set of column names for a SQLAlchemy model."""
    return {c.key for c in model.__table__.columns}


def _sanitise(val):
    """Convert NaN float values to None for SQLAlchemy compatibility."""
    import math
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def ingest_speedtest(db: Session | None = None) -> None:
    """
    Parse the speedtest CSV log and persist new records to the database.

    Reads from LOG_PATH, coerces numeric columns, deduplicates against
    the latest stored timestamp, and routes each row to either
    SpeedTestResult (status ONLINE, all metrics present) or
    SpeedTestFailure (failed or incomplete).

    Performance status is classified using thresholds from the settings
    table at the time of ingest.

    Args:
        db: Optional database session. If not provided, a new session is
            created and closed automatically. Pass an existing session in
            tests to avoid patching SessionLocal.
    """
    _owns_db = db is None
    if _owns_db:
        db = SessionLocal()
    try:
        thresholds = _get_thresholds(db)

        df = pd.read_csv(
            LOG_PATH,
            header=None,
            names=[
                "timestamp", "status", "ping", "download_mbps",
                "upload_mbps", "server_name", "server_id", "distance",
                "failure_reason",
            ],
        )

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["ping", "download_mbps", "upload_mbps", "distance"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Deduplicate — only ingest records newer than the latest stored timestamp
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
        latest_timestamps = [t for t in [latest_result, latest_failure] if t is not None]
        latest_timestamp = max(latest_timestamps) if latest_timestamps else None

        if latest_timestamp is not None:
            df = df[df["timestamp"] > latest_timestamp]

        if df.empty:
            return

        for _, row in df.iterrows():
            is_success = (
                row["status"] == "ONLINE"
                and pd.notna(row["download_mbps"])
                and pd.notna(row["upload_mbps"])
                and pd.notna(row["ping"])
            )

            data = {
                k: _sanitise(v)
                for k, v in row.items()
                if k != "failure_reason"
            }

            if is_success:
                db.add(SpeedTestResult(
                    **{k: v for k, v in data.items() if k in _columns_for(SpeedTestResult)},
                    performance_status=classify_speed(
                        row["download_mbps"],
                        row["upload_mbps"],
                        thresholds,
                    ),
                ))
            else:
                db.add(SpeedTestFailure(
                    **{k: v for k, v in data.items() if k in _columns_for(SpeedTestFailure)},
                    failure_reason=_sanitise(row.get("failure_reason")),
                ))

        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        if _owns_db:
            db.close()


def reclassify_all(db: Session) -> int:
    """
    Re-run performance classification over all stored SpeedTestResult rows
    using the current threshold settings.

    Useful after changing thresholds in the settings UI — existing rows
    retain their old classification until this is called.

    Returns the number of rows updated.
    """
    thresholds = _get_thresholds(db)
    results = db.query(SpeedTestResult).all()
    count = 0
    for result in results:
        new_status = classify_speed(
            result.download_mbps,
            result.upload_mbps,
            thresholds,
        )
        if result.performance_status != new_status:
            result.performance_status = new_status
            count += 1
    db.commit()
    return count