import math
import pandas as pd
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.connectivity import ConnectivityCheck
from services.connectivity_service import get_latest_timestamp
from pathlib import Path

LOG_PATH = Path("/mnt/media/monitoring/data/connectivity.csv")

COLUMNS = ["timestamp", "status", "latency_ms"]


def _sanitise(data: dict) -> dict:
    """Replace float NaN values with None for SQLAlchemy compatibility."""
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in data.items()
    }


def ingest_connectivity():
    """
    Read the connectivity check CSV log and insert only records newer than
    the latest stored timestamp.

    All rows are inserted into a single table regardless of status, since
    failed checks (NO INTERNET) have no missing metrics — just a null latency.
    Deduplication is handled by comparing against the latest stored timestamp.

    CSV format (headerless, 3 columns):
        timestamp, status, latency_ms

    Raises:
        FileNotFoundError: If LOG_PATH does not exist.
        sqlalchemy.exc.SQLAlchemyError: If the database commit fails.
    """
    df = pd.read_csv(
        LOG_PATH,
        header=0,
        names=COLUMNS,
        parse_dates=["timestamp"],
        on_bad_lines="skip",
        engine="python",
    )

    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")

    db: Session = SessionLocal()

    try:
        latest_timestamp = get_latest_timestamp(db)

        if latest_timestamp is not None:
            df = df[df["timestamp"] > pd.Timestamp(latest_timestamp)]

        if df.empty:
            return

        for _, row in df.iterrows():
            data = _sanitise(row.to_dict())
            db.add(ConnectivityCheck(**data))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()