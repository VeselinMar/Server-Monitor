from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServerHealthCreate(BaseModel):
    timestamp: datetime

    # CPU
    cpu_percent: float | None = None
    load_1: float | None = None
    load_5: float | None = None
    load_15: float | None = None

    # Memory
    memory_total_bytes: int | None = None
    memory_available_bytes: int | None = None
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None

    # Temperature
    cpu_package_temp_c: float | None = None
    cpu_core0_temp_c: float | None = None
    cpu_core1_temp_c: float | None = None

    # Disk I/O
    disk_read_bytes: int | None = None
    disk_write_bytes: int | None = None
    disk_read_iops: float | None = None
    disk_write_iops: float | None = None
    disk_util_percent: float | None = None

    # Network
    network_rx_bytes: int | None = None
    network_tx_bytes: int | None = None
    network_rx_errors: int | None = None
    network_tx_errors: int | None = None
    network_rx_drops: int | None = None
    network_tx_drops: int | None = None

    # System
    uptime_seconds: float | None = None


class ServerHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime

    # CPU
    cpu_percent: float | None = None
    load_1: float | None = None
    load_5: float | None = None
    load_15: float | None = None

    # Memory
    memory_total_bytes: int | None = None
    memory_available_bytes: int | None = None
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None

    # Temperature
    cpu_package_temp_c: float | None = None
    cpu_core0_temp_c: float | None = None
    cpu_core1_temp_c: float | None = None

    # Disk I/O
    disk_read_bytes: int | None = None
    disk_write_bytes: int | None = None
    disk_read_iops: float | None = None
    disk_write_iops: float | None = None
    disk_util_percent: float | None = None

    # Network
    network_rx_bytes: int | None = None
    network_tx_bytes: int | None = None
    network_rx_errors: int | None = None
    network_tx_errors: int | None = None
    network_rx_drops: int | None = None
    network_tx_drops: int | None = None

    # System
    uptime_seconds: float | None = None
