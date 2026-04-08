from __future__ import annotations

from dataclasses import dataclass

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None


@dataclass
class SerialDevice:
    port: str
    description: str
    hwid: str


class HardwareInterfaceWrapper:
    """Read-only hardware wrapper.

    This class only discovers and reports telemetry interfaces exposed by the
    existing firmware. It never writes firmware or sends control commands.
    """

    @staticmethod
    def list_serial_devices() -> list[SerialDevice]:
        if list_ports is None:
            return []

        devices: list[SerialDevice] = []
        for info in list_ports.comports():
            devices.append(
                SerialDevice(
                    port=info.device,
                    description=info.description or "",
                    hwid=info.hwid or "",
                )
            )
        return devices

    @classmethod
    def auto_detect_serial_port(cls) -> str | None:
        devices = cls.list_serial_devices()
        if not devices:
            return None

        for device in devices:
            descriptor = f"{device.description} {device.hwid}".lower()
            if any(token in descriptor for token in ("usb", "uart", "cp210", "ch340", "esp32", "arduino")):
                return device.port

        return devices[0].port
