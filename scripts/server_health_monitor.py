#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import psutil


API_URL = os.getenv(
    "SERVER_HEALTH_API_URL",
    "http://127.0.0.1/servermonitor/server/health",
)

API_TOKEN = os.getenv("SERVER_HEALTH_API_TOKEN")

DISK_INTERVAL_SECONDS = float(
    os.getenv("SERVER_HEALTH_DISK_INTERVAL", "1.0")
)


def get_cpu_temperature() -> tuple[
    float | None,
    float | None,
    float | None,
]:
    """
    Best-effort CPU temperature discovery.

    Returns:
        (package_temperature, core0_temperature, core1_temperature)

    Temperature sensors vary considerably between Linux systems.
    Missing sensors are represented by None rather than causing
    collection to fail.
    """
    try:
        sensors = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None, None, None

    if not sensors:
        return None, None, None

    preferred = (
        "coretemp",
        "k10temp",
        "zenpower",
        "cpu_thermal",
        "x86_pkg_temp",
    )

    entries = []

    for name in preferred:
        if name in sensors:
            entries.extend(sensors[name])

    # Fall back to any available temperature sensor.
    if not entries:
        for sensor_entries in sensors.values():
            entries.extend(sensor_entries)

    package_temp = None
    core_temps: list[float] = []

    for entry in entries:
        if entry.current is None:
            continue

        temperature = float(entry.current)
        label = (entry.label or "").lower()

        if package_temp is None and (
            "package" in label
            or "tctl" in label
            or "tdie" in label
            or "cpu" in label
        ):
            package_temp = temperature

        if "core" in label:
            core_temps.append(temperature)

    # If there is no explicit package reading, use the first
    # available CPU sensor as the package-like value.
    if package_temp is None:
        for entry in entries:
            if entry.current is not None:
                package_temp = float(entry.current)
                break

    core0 = core_temps[0] if len(core_temps) > 0 else None
    core1 = core_temps[1] if len(core_temps) > 1 else None

    return package_temp, core0, core1


def get_disk_io_snapshot() -> dict:
    """
    Return per-device disk I/O counters.

    The raw counters are retained so interval rates can be calculated
    between two snapshots.
    """
    try:
        return psutil.disk_io_counters(perdisk=True) or {}
    except (AttributeError, OSError):
        return {}


def calculate_disk_rates(
    before: dict,
    after: dict,
    elapsed: float,
) -> tuple[
    float | None,
    float | None,
    float | None,
]:
    """
    Calculate aggregate read IOPS, write IOPS and disk utilisation.

    IOPS are based on completed read/write operations during the
    measurement interval.

    Disk utilisation is based on cumulative device busy time reported
    by psutil.
    """
    if elapsed <= 0:
        return None, None, None

    read_count = 0
    write_count = 0
    busy_ms = 0

    devices = set(before) | set(after)

    for device in devices:
        old = before.get(device)
        new = after.get(device)

        # Ignore devices that appeared or disappeared during the
        # measurement interval.
        if old is None or new is None:
            continue

        read_count += max(
            0,
            new.read_count - old.read_count,
        )

        write_count += max(
            0,
            new.write_count - old.write_count,
        )

        busy_ms += max(
            0,
            new.busy_time - old.busy_time,
        )

    read_iops = read_count / elapsed
    write_iops = write_count / elapsed

    # busy_time is reported in milliseconds.
    utilization = (
        busy_ms
        / (elapsed * 1000)
        * 100
    )

    # Multiple devices can theoretically produce an aggregate busy
    # time greater than the wall-clock interval.
    utilization = min(100.0, utilization)

    return (
        round(read_iops, 2),
        round(write_iops, 2),
        round(utilization, 2),
    )


def get_disk_counters() -> tuple[
    int | None,
    int | None,
]:
    """
    Return cumulative disk bytes read/written across all devices.

    No device name is assumed, so this works with SATA, NVMe, USB,
    virtual disks, etc.
    """
    try:
        counters = psutil.disk_io_counters(perdisk=True)
    except (AttributeError, OSError):
        return None, None

    if not counters:
        return None, None

    read_bytes = 0
    write_bytes = 0

    for counter in counters.values():
        read_bytes += counter.read_bytes
        write_bytes += counter.write_bytes

    return read_bytes, write_bytes


def get_network_counters() -> tuple[
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
]:
    """
    Return cumulative network counters across all non-loopback
    interfaces.

    Returns:
        rx_bytes,
        tx_bytes,
        rx_errors,
        tx_errors,
        rx_drops,
        tx_drops
    """
    try:
        counters = psutil.net_io_counters(pernic=True)
    except (AttributeError, OSError):
        return (None,) * 6

    if not counters:
        return (None,) * 6

    rx_bytes = 0
    tx_bytes = 0
    rx_errors = 0
    tx_errors = 0
    rx_drops = 0
    tx_drops = 0

    found = False

    for interface, counter in counters.items():
        if interface == "lo":
            continue

        found = True

        rx_bytes += counter.bytes_recv
        tx_bytes += counter.bytes_sent

        rx_errors += counter.errin
        tx_errors += counter.errout

        rx_drops += counter.dropin
        tx_drops += counter.dropout

    if not found:
        return (None,) * 6

    return (
        rx_bytes,
        tx_bytes,
        rx_errors,
        tx_errors,
        rx_drops,
        tx_drops,
    )


def get_uptime() -> float | None:
    """
    Return system uptime in seconds.

    psutil.boot_time() is used instead of assuming /proc/uptime exists.
    """
    try:
        return max(
            0.0,
            time.time() - psutil.boot_time(),
        )
    except (AttributeError, OSError):
        return None


def collect_snapshot() -> dict:
    """
    Collect one point-in-time host health snapshot.

    Hardware-specific metrics are best-effort. If a metric is not
    available on the host, its value is represented by None.
    """

    # CPU
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
    except (AttributeError, OSError):
        cpu_percent = None

    try:
        load_1, load_5, load_15 = psutil.getloadavg()
    except (AttributeError, OSError):
        load_1 = None
        load_5 = None
        load_15 = None

    # Memory
    try:
        memory = psutil.virtual_memory()

        memory_total = memory.total
        memory_available = memory.available

    except (AttributeError, OSError):
        memory_total = None
        memory_available = None

    # Swap
    try:
        swap = psutil.swap_memory()

        swap_total = swap.total
        swap_used = swap.used

    except (AttributeError, OSError):
        swap_total = None
        swap_used = None

    # CPU temperature
    (
        cpu_package_temp,
        cpu_core0_temp,
        cpu_core1_temp,
    ) = get_cpu_temperature()

    # Disk
    disk_read_bytes, disk_write_bytes = get_disk_counters()

    # Network
    (
        network_rx_bytes,
        network_tx_bytes,
        network_rx_errors,
        network_tx_errors,
        network_rx_drops,
        network_tx_drops,
    ) = get_network_counters()

    # System
    uptime_seconds = get_uptime()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "cpu_percent": cpu_percent,
        "load_1": load_1,
        "load_5": load_5,
        "load_15": load_15,

        "memory_total_bytes": memory_total,
        "memory_available_bytes": memory_available,

        "swap_total_bytes": swap_total,
        "swap_used_bytes": swap_used,

        "cpu_package_temp_c": cpu_package_temp,
        "cpu_core0_temp_c": cpu_core0_temp,
        "cpu_core1_temp_c": cpu_core1_temp,

        "disk_read_bytes": disk_read_bytes,
        "disk_write_bytes": disk_write_bytes,

        # Interval metrics are populated by collect_health().
        "disk_read_iops": None,
        "disk_write_iops": None,
        "disk_util_percent": None,

        "network_rx_bytes": network_rx_bytes,
        "network_tx_bytes": network_tx_bytes,

        "network_rx_errors": network_rx_errors,
        "network_tx_errors": network_tx_errors,

        "network_rx_drops": network_rx_drops,
        "network_tx_drops": network_tx_drops,

        "uptime_seconds": uptime_seconds,
    }


def collect_health() -> dict:
    """
    Collect a complete server-health sample.

    Two disk I/O snapshots are taken around the configured interval
    so that read IOPS, write IOPS and disk utilisation can be derived.
    """

    before = get_disk_io_snapshot()

    start = time.monotonic()

    time.sleep(DISK_INTERVAL_SECONDS)

    after = get_disk_io_snapshot()

    elapsed = time.monotonic() - start

    payload = collect_snapshot()

    (
        payload["disk_read_iops"],
        payload["disk_write_iops"],
        payload["disk_util_percent"],
    ) = calculate_disk_rates(
        before,
        after,
        elapsed,
    )

    return payload


def send(payload: dict) -> None:
    """
    Submit a health payload to the ServerMonitor API.
    """

    if not API_TOKEN:
        raise RuntimeError(
            "SERVER_HEALTH_API_TOKEN is not configured"
        )

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:

            if response.status < 200 or response.status >= 300:
                raise RuntimeError(
                    f"Server health API returned "
                    f"HTTP {response.status}"
                )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Server health API returned "
            f"HTTP {exc.code}: {body}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach server health API: "
            f"{exc.reason}"
        ) from exc


def main() -> int:
    """
    Collect and submit one server-health sample.
    """

    try:
        payload = collect_health()

        send(payload)

        print(
            "Server health submitted successfully"
        )

        return 0

    except Exception as exc:
        print(
            f"Server health collection failed: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
