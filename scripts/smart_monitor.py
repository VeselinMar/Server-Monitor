import json
import shutil
import subprocess


def collect_smart_health() -> list[dict]:
    """Collect selected SMART health metrics from physical disks.

    SMART collection is best-effort. Any individual device or command
    failure is skipped without affecting the rest of server monitoring.
    """
    if shutil.which("smartctl") is None:
        return []

    try:
        scan_result = subprocess.run(
            ["sudo", "-n", "/usr/sbin/smartctl", "--scan-open", "-j"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    try:
        scan_data = json.loads(scan_result.stdout)
    except (json.JSONDecodeError, TypeError):
        return []

    devices = scan_data.get("devices", [])
    if not isinstance(devices, list):
        return []

    smart_devices = []

    for discovered in devices:
        if not isinstance(discovered, dict):
            continue

        # --scan-open can report devices that the current user cannot open.
        if discovered.get("open_error"):
            continue

        device = discovered.get("name")
        device_type = discovered.get("type")

        if not device:
            continue
                
        command = [
            "sudo",
            "-n",
            "/usr/sbin/smartctl",
            "-a",
            "-j",
        ]


        if device_type:
            command.extend(["-d", device_type])

        command.append(device)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(data, dict):
            continue

        temperature = None
        power_on_hours = None
        reallocated_sectors = None
        pending_sectors = None
        uncorrectable_sectors = None

        # These are available for both ATA and NVMe in smartctl JSON.
        temperature_data = data.get("temperature")
        if isinstance(temperature_data, dict):
            temperature = temperature_data.get("current")

        power_on_time = data.get("power_on_time")
        if isinstance(power_on_time, dict):
            power_on_hours = power_on_time.get("hours")

        # ATA/SATA SMART attributes.
        if device_type != "nvme":
            smart_attributes = data.get("ata_smart_attributes", {})
            table = smart_attributes.get("table", [])

            if isinstance(table, list):
                for attribute in table:
                    if not isinstance(attribute, dict):
                        continue

                    attribute_id = attribute.get("id")
                    raw = attribute.get("raw")

                    if not isinstance(raw, dict):
                        continue

                    raw_value = raw.get("value")

                    if raw_value is None:
                        continue

                    if attribute_id == 5:
                        reallocated_sectors = raw_value
                    elif attribute_id == 197:
                        pending_sectors = raw_value
                    elif attribute_id == 198:
                        uncorrectable_sectors = raw_value

        # NVMe has no ATA-style reallocated/pending counters.
        # media_errors is the closest equivalent to uncorrectable/media errors.
        else:
            nvme_health = data.get(
                "nvme_smart_health_information_log",
                {},
            )

            if isinstance(nvme_health, dict):
                uncorrectable_sectors = nvme_health.get("media_errors")

        smart_devices.append(
            {
                "device": device,
                "model": data.get("model_name"),
                "temperature_c": temperature,
                "reallocated_sectors": reallocated_sectors,
                "pending_sectors": pending_sectors,
                "uncorrectable_sectors": uncorrectable_sectors,
                "power_on_hours": power_on_hours,
            }
        )

    return smart_devices
