from unittest.mock import patch
from datetime import datetime, timedelta

from models.server_health import ServerHealth
from services import server_health_service



def make_health(timestamp: datetime, cpu: float) -> ServerHealth:
    return ServerHealth(
        timestamp=timestamp,
        cpu_percent=cpu,
        load_1=1.0,
        load_5=0.8,
        load_15=0.6,
        memory_total_bytes=16_000_000_000,
        memory_available_bytes=8_000_000_000,
        swap_total_bytes=4_000_000_000,
        swap_used_bytes=100_000_000,
        cpu_package_temp_c=45.0,
        cpu_core0_temp_c=44.0,
        cpu_core1_temp_c=46.0,
        disk_read_bytes=100_000,
        disk_write_bytes=200_000,
        disk_read_iops=10.0,
        disk_write_iops=20.0,
        disk_util_percent=5.0,
        network_rx_bytes=1_000_000,
        network_tx_bytes=2_000_000,
        network_rx_errors=0,
        network_tx_errors=0,
        network_rx_drops=0,
        network_tx_drops=0,
        uptime_seconds=86_400.0,
    )


def test_create_and_get_latest(db):
    timestamp = datetime(2026, 8, 27, 10, 0, 0)

    health = make_health(timestamp, 25.0)

    created = server_health_service.create(db, health)

    assert created.id is not None
    assert created.cpu_percent == 25.0

    latest = server_health_service.get_latest(db)

    assert latest is not None
    assert latest.id == created.id
    assert latest.cpu_percent == 25.0


def test_get_latest_returns_newest_record(db):
    first = make_health(
        datetime(2026, 8, 27, 10, 0, 0),
        20.0,
    )

    second = make_health(
        datetime(2026, 8, 27, 10, 5, 0),
        80.0,
    )

    server_health_service.create(db, first)
    server_health_service.create(db, second)

    latest = server_health_service.get_latest(db)

    assert latest is not None
    assert latest.cpu_percent == 80.0


def test_get_history_returns_chronological_records(db):
    base = datetime(2026, 8, 27, 10, 0, 0)

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=10), 30.0),
    )

    server_health_service.create(
        db,
        make_health(base, 20.0),
    )

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=20), 40.0),
    )

    history = server_health_service.get_history(
        db,
        base,
        base + timedelta(minutes=20),
    )

    assert len(history) == 3
    assert [item.cpu_percent for item in history] == [
        20.0,
        30.0,
        40.0,
    ]


def test_get_history_filters_time_range(db):
    base = datetime(2026, 8, 27, 10, 0, 0)

    server_health_service.create(
        db,
        make_health(base, 10.0),
    )

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=10), 20.0),
    )

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=20), 30.0),
    )

    history = server_health_service.get_history(
        db,
        base + timedelta(minutes=5),
        base + timedelta(minutes=15),
    )

    assert len(history) == 1
    assert history[0].cpu_percent == 20.0


def test_latest_endpoint(client, db):
    health = make_health(
        datetime(2026, 8, 27, 11, 0, 0),
        42.0,
    )

    server_health_service.create(db, health)

    response = client.get("/server/health/latest")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == health.id
    assert data["cpu_percent"] == 42.0
    assert data["memory_total_bytes"] == 16_000_000_000
    assert data["uptime_seconds"] == 86_400.0


def test_latest_endpoint_returns_404_when_empty(client):
    response = client.get("/server/health/latest")

    assert response.status_code == 404


def test_history_endpoint(client, db):
    base = datetime(2026, 8, 27, 11, 0, 0)

    server_health_service.create(
        db,
        make_health(base, 20.0),
    )

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=10), 40.0),
    )

    server_health_service.create(
        db,
        make_health(base + timedelta(minutes=20), 60.0),
    )

    response = client.get(
        "/server/health/history",
        params={
            "from_dt": base.isoformat(),
            "to_dt": (base + timedelta(minutes=20)).isoformat(),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert [item["cpu_percent"] for item in data] == [
        20.0,
        40.0,
        60.0,
    ]


def test_history_endpoint_requires_dates(client):
    response = client.get("/server/health/history")

    assert response.status_code == 422
