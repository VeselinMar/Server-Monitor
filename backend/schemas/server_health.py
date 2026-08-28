from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class ServerHealthCreate(BaseModel):
    timestamp: datetime

    # CPU
    cpu_percent: float | None = None
    cpu_per_core_percent: list[float] | None = None
    cpu_frequency_mhz: float | None = None
    load_1: float | None = None
    load_5: float | None = None
    load_15: float | None = None

    # Memory
    memory_total_bytes: int | None = None
    memory_used_bytes: int | None = None
    memory_available_bytes: int | None = None
    memory_cached_bytes: int | None = None
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None
    swap_sin_bytes: int | None = None
    swap_sout_bytes: int | None = None


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

    # Filesystem
    filesystems: list[dict[str, Any]] = Field(default_factory=list)

    smart_devices: list[dict[str, Any]] = Field(
        default_factory=list
    )



class ServerHealthFilesystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_health_id: int
    mountpoint: str

    capacity_status: str
    inode_status: str

    total_bytes: int | None = None
    used_bytes: int | None = None
    available_bytes: int | None = None
    percent: float | None = None

    inode_total: int | None = None
    inode_used: int | None = None
    inode_free: int | None = None
    inode_percent: float | None = None


class ServerHealthSmartDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_health_id: int

    device: str
    model: str | None = None

    temperature_c: float | None = None

    reallocated_sectors: int | None = None
    pending_sectors: int | None = None
    uncorrectable_sectors: int | None = None

    power_on_hours: int | None = None


class ServerHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime

    # CPU
    cpu_percent: float | None = None
    cpu_per_core_percent: list[float] | None = None
    cpu_frequency_mhz: float | None = None
    load_1: float | None = None
    load_5: float | None = None
    load_15: float | None = None



    # Memory
    memory_total_bytes: int | None = None
    memory_used_bytes: int | None = None
    memory_available_bytes: int | None = None
    memory_cached_bytes: int | None = None
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None
    swap_sin_bytes: int | None = None
    swap_sout_bytes: int | None = None


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

    # Filesystem
    filesystems: list[ServerHealthFilesystemResponse] = Field(
        default_factory=list
    )

    # SMART
    smart_devices: list[ServerHealthSmartDeviceResponse] = Field(
    default_factory=list
    )
