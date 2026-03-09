"""
Pytest configuration and shared fixtures for ServerMonitor backend tests.

Uses an in-memory SQLite database so tests are fully isolated and leave
no files on disk. The FastAPI test client is provided as a session-scoped
fixture to avoid repeated app startup overhead.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date, timedelta

from core.database import Base
from main import app


# ── In-memory test database ───────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the entire test session."""
    import models.speedtest       # noqa: F401
    import models.connectivity    # noqa: F401
    import models.daily_summary   # noqa: F401
    import models.settings        # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """
    Provide a clean database session per test, rolling back after each test
    so tests do not bleed state into one another.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """
    FastAPI test client with the database dependency overridden to use the
    per-test in-memory session.

    Each route module defines its own local get_db, so we override each one.
    """
    from api.routes import speedtest, connectivity, summary, report
    from api.routes import settings as settings_route

    def override_get_db():
        yield db

    for module in [speedtest, connectivity, summary, report, settings_route]:
        app.dependency_overrides[module.get_db] = override_get_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Shared test data factories ────────────────────────────────────────────────

from models.speedtest     import SpeedTestResult, SpeedTestFailure
from models.connectivity  import ConnectivityCheck
from models.daily_summary import DailySummary
from models.settings      import Setting


def make_speedtest_result(db, **kwargs):
    """Insert a SpeedTestResult with sensible defaults."""
    defaults = dict(
        timestamp          = datetime(2026, 2, 1, 12, 0, 0),
        status             = "ONLINE",
        ping               = 15.0,
        download_mbps      = 120.0,
        upload_mbps        = 10.0,
        server_name        = "Vienna Test Server",
        server_id          = "1234",
        distance           = 5.0,
        performance_status = "NORMAL",
    )
    defaults.update(kwargs)
    obj = SpeedTestResult(**defaults)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def make_speedtest_failure(db, **kwargs):
    """Insert a SpeedTestFailure with sensible defaults."""
    defaults = dict(
        timestamp      = datetime(2026, 2, 1, 13, 0, 0),
        status         = "FAILED",
        failure_reason = "timeout",
    )
    defaults.update(kwargs)
    obj = SpeedTestFailure(**defaults)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def make_connectivity_check(db, **kwargs):
    """Insert a ConnectivityCheck with sensible defaults."""
    defaults = dict(
        timestamp  = datetime(2026, 2, 1, 12, 0, 0),
        status     = "ONLINE",
        latency_ms = 12.0,
    )
    defaults.update(kwargs)
    obj = ConnectivityCheck(**defaults)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def make_daily_summary(db, **kwargs):
    """Insert a DailySummary with sensible defaults."""
    defaults = dict(
        period_date          = date(2026, 2, 1),
        avg_download_mbps    = 110.0,
        min_download_mbps    = 80.0,
        avg_upload_mbps      = 9.0,
        avg_ping             = 14.0,
        successful_tests     = 8,
        failed_tests         = 0,
        total_tests          = 8,
        outage_count         = 0,
        outage_total_minutes = 0,
    )
    defaults.update(kwargs)
    obj = DailySummary(**defaults)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def make_setting(db, key, value):
    """Insert a Setting row."""
    obj = Setting(key=key, value=value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj