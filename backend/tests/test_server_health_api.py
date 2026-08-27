from models.server_health import ServerHealth

headers = {
    "Authorization": "Bearer test-server-health-token",
}

def health_payload(**overrides):
    payload = {
        "timestamp": "2026-08-27T12:00:00Z",
        "cpu_percent": 25.5,
        "load_1": 1.2,
        "load_5": 1.0,
        "load_15": 0.8,
        "memory_total_bytes": 16_000_000_000,
        "memory_available_bytes": 8_000_000_000,
        "swap_total_bytes": 4_000_000_000,
        "swap_used_bytes": 100_000_000,
        "cpu_package_temp_c": 55.0,
        "cpu_core0_temp_c": 54.0,
        "cpu_core1_temp_c": 56.0,
        "disk_read_bytes": 1_000_000,
        "disk_write_bytes": 2_000_000,
        "disk_read_iops": 10.5,
        "disk_write_iops": 5.5,
        "disk_util_percent": 12.5,
        "network_rx_bytes": 100_000_000,
        "network_tx_bytes": 50_000_000,
        "network_rx_errors": 0,
        "network_tx_errors": 0,
        "network_rx_drops": 0,
        "network_tx_drops": 0,
        "uptime_seconds": 100_000.0,
    }

    payload.update(overrides)
    return payload


def test_create_server_health(client):
    response = client.post(
        "/server/health",
        json=health_payload(),
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["cpu_percent"] == 25.5
    assert data["memory_total_bytes"] == 16_000_000_000
    assert data["cpu_package_temp_c"] == 55.0
    assert data["disk_read_iops"] == 10.5
    assert data["network_rx_bytes"] == 100_000_000


def test_create_server_health_persists_data(client, db):
    response = client.post(
        "/server/health",
        json=health_payload(cpu_percent=73.2),
        headers=headers,
    )

    assert response.status_code == 201

    health = (
        db.query(ServerHealth)
        .filter(ServerHealth.id == response.json()["id"])
        .first()
    )

    assert health is not None
    assert health.cpu_percent == 73.2


def test_create_server_health_accepts_missing_optional_fields(client):
    response = client.post(
        "/server/health",
        json={
            "timestamp": "2026-08-27T12:00:00Z",
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["cpu_percent"] is None
    assert data["memory_total_bytes"] is None
    assert data["cpu_package_temp_c"] is None
    assert data["disk_read_iops"] is None
    assert data["network_rx_bytes"] is None


def test_create_server_health_rejects_missing_timestamp(client):
    response = client.post(
        "/server/health",
        json={
            "cpu_percent": 25.0,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_server_health_rejects_invalid_timestamp(client):
    response = client.post(
        "/server/health",
        json={
            "timestamp": "not-a-timestamp",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_server_health_latest_returns_created_sample(client):
    response = client.post(
        "/server/health",
        json=health_payload(
            timestamp="2026-08-27T12:00:00Z",
            cpu_percent=42.0,
        ),
        headers=headers,
    )

    assert response.status_code == 201

    response = client.get("/server/health/latest")

    assert response.status_code == 200

    data = response.json()

    assert data["cpu_percent"] == 42.0



def test_create_server_health_history_returns_samples(client):
    response = client.post(
        "/server/health",
        json=health_payload(
            timestamp="2026-08-27T12:00:00Z",
            cpu_percent=20.0,
        ),
        headers=headers,
    )

    assert response.status_code == 201

    response = client.post(
        "/server/health",
        json=health_payload(
            timestamp="2026-08-27T12:05:00Z",
            cpu_percent=30.0,
        ),
        headers=headers,
    )

    assert response.status_code == 201


    response = client.get(
        "/server/health/history",
        params={
            "from_dt": "2026-08-27T11:00:00Z",
            "to_dt": "2026-08-27T13:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [item["cpu_percent"] for item in data] == [20.0, 30.0]
