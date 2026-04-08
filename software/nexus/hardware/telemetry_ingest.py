from __future__ import annotations

import json
import select
import socket
from datetime import datetime, timezone
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from nexus.db.database import DatabaseManager
from nexus.hardware.interface import HardwareInterfaceWrapper

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover
    serial = None

    class SerialException(Exception):
        pass


class TelemetrySchemaValidator:
    """Safe schema normalizer for inbound telemetry JSON."""

    @staticmethod
    def _normalize_timestamp(value: Any) -> str:
        if value is None or value == "":
            return datetime.now(timezone.utc).isoformat()

        if isinstance(value, (int, float)):
            try:
                epoch = float(value)
                if epoch > 1e12:
                    epoch = epoch / 1000.0
                return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
            except (OverflowError, OSError, ValueError):
                return datetime.now(timezone.utc).isoformat()

        return str(value)

    def validate(self, payload: Any, source: str, channel: str) -> tuple[bool, dict[str, Any], str]:
        if not isinstance(payload, dict):
            return False, {}, "Telemetry must be a JSON object"

        normalized = dict(payload)
        normalized["timestamp"] = self._normalize_timestamp(normalized.get("timestamp"))
        normalized["device_id"] = str(
            normalized.get("device_id")
            or normalized.get("device")
            or normalized.get("id")
            or "unknown-device"
        )
        normalized["source"] = str(normalized.get("source") or source)
        normalized["channel"] = str(normalized.get("channel") or channel)

        network = normalized.get("network")
        if not isinstance(network, dict):
            network = {}
        normalized["network"] = {
            "ip": str(network.get("ip") or ""),
            "mac": str(network.get("mac") or ""),
        }

        metrics = normalized.get("metrics")
        if not isinstance(metrics, dict):
            metrics = {}
        normalized["metrics"] = metrics

        events = normalized.get("events")
        if isinstance(events, list):
            normalized["events"] = events
        else:
            normalized["events"] = []

        return True, normalized, ""


class SerialListenerThread(QThread):
    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, port: str = "", baudrate: int = 115200) -> None:
        super().__init__()
        self._port = port
        self._baudrate = baudrate
        self._running = False
        self._serial_handle = None

    def run(self) -> None:
        if serial is None:
            self.error.emit("pyserial is not installed; serial ingest is unavailable")
            self.status_changed.emit(False, "Serial unavailable")
            return

        port = self._port or HardwareInterfaceWrapper.auto_detect_serial_port()
        if not port:
            self.status_changed.emit(False, "No serial telemetry device detected")
            return

        self._running = True
        try:
            self._serial_handle = serial.Serial(port=port, baudrate=self._baudrate, timeout=1)
            self.status_changed.emit(True, f"Serial connected: {port}")

            while self._running:
                try:
                    raw = self._serial_handle.readline()
                except SerialException as exc:
                    self.error.emit(f"Serial read error: {exc}")
                    break

                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if line:
                    self.line_received.emit(line)

        except (OSError, SerialException) as exc:
            self.error.emit(f"Serial connection failed: {exc}")
        finally:
            if self._serial_handle is not None:
                try:
                    self._serial_handle.close()
                except OSError:
                    pass
                self._serial_handle = None
            self.status_changed.emit(False, "Serial stopped")
            self._running = False

    def stop(self) -> None:
        self._running = False
        if self._serial_handle is not None:
            try:
                self._serial_handle.close()
            except OSError:
                pass
        self.wait(1500)


class TcpListenerThread(QThread):
    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._running = False

    def run(self) -> None:
        self._running = True
        server: socket.socket | None = None
        clients: list[socket.socket] = []
        buffers: dict[socket.socket, bytes] = {}

        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self._host, self._port))
            server.listen(5)
            server.setblocking(False)
            self.status_changed.emit(True, f"TCP listening on {self._host}:{self._port}")

            while self._running:
                watch = [server, *clients]
                readable, _, exceptional = select.select(watch, [], watch, 0.5)

                for sock in readable:
                    if sock is server:
                        client, addr = server.accept()
                        client.setblocking(False)
                        clients.append(client)
                        buffers[client] = b""
                        self.status_changed.emit(True, f"TCP client connected: {addr[0]}:{addr[1]}")
                    else:
                        try:
                            data = sock.recv(4096)
                        except OSError:
                            data = b""

                        if not data:
                            buffers.pop(sock, None)
                            if sock in clients:
                                clients.remove(sock)
                            try:
                                sock.close()
                            except OSError:
                                pass
                            continue

                        buffers[sock] = buffers.get(sock, b"") + data
                        while b"\n" in buffers[sock]:
                            line, remaining = buffers[sock].split(b"\n", 1)
                            buffers[sock] = remaining
                            text = line.decode("utf-8", errors="ignore").strip()
                            if text:
                                self.line_received.emit(text)

                for sock in exceptional:
                    buffers.pop(sock, None)
                    if sock in clients:
                        clients.remove(sock)
                    try:
                        sock.close()
                    except OSError:
                        pass

        except OSError as exc:
            self.error.emit(f"TCP listener error: {exc}")
        finally:
            for client in clients:
                try:
                    client.close()
                except OSError:
                    pass
            if server is not None:
                try:
                    server.close()
                except OSError:
                    pass
            self.status_changed.emit(False, "TCP listener stopped")
            self._running = False

    def stop(self) -> None:
        self._running = False
        self.wait(1500)


class TelemetryIngestManager(QObject):
    raw_line_received = pyqtSignal(str)
    telemetry_received = pyqtSignal(dict)
    telemetry_invalid = pyqtSignal(str)
    connection_state = pyqtSignal(str, bool, str)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._db = database
        self._validator = TelemetrySchemaValidator()
        self._serial_thread: SerialListenerThread | None = None
        self._tcp_thread: TcpListenerThread | None = None

    def start_serial(self, port: str = "", baudrate: int = 115200) -> None:
        if self._serial_thread and self._serial_thread.isRunning():
            self.connection_state.emit("serial", True, "Serial listener already running")
            return

        thread = SerialListenerThread(port=port, baudrate=baudrate)
        thread.line_received.connect(lambda line: self._handle_line("serial", line))
        thread.error.connect(lambda message: self.telemetry_invalid.emit(message))
        thread.status_changed.connect(
            lambda connected, message: self.connection_state.emit("serial", connected, message)
        )
        self._serial_thread = thread
        thread.start()

    def stop_serial(self) -> None:
        if self._serial_thread:
            self._serial_thread.stop()
            self._serial_thread = None

    def start_tcp(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        if self._tcp_thread and self._tcp_thread.isRunning():
            self.connection_state.emit("tcp", True, "TCP listener already running")
            return

        thread = TcpListenerThread(host=host, port=port)
        thread.line_received.connect(lambda line: self._handle_line("tcp", line))
        thread.error.connect(lambda message: self.telemetry_invalid.emit(message))
        thread.status_changed.connect(
            lambda connected, message: self.connection_state.emit("tcp", connected, message)
        )
        self._tcp_thread = thread
        thread.start()

    def stop_tcp(self) -> None:
        if self._tcp_thread:
            self._tcp_thread.stop()
            self._tcp_thread = None

    def stop_all(self) -> None:
        self.stop_serial()
        self.stop_tcp()

    def _handle_line(self, source: str, line: str) -> None:
        self.raw_line_received.emit(f"[{source}] {line}")

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            self.telemetry_invalid.emit(f"Invalid JSON from {source}: {line[:120]}")
            return

        valid, telemetry, error = self._validator.validate(payload, source=source, channel=source)
        if not valid:
            self.telemetry_invalid.emit(f"Invalid telemetry from {source}: {error}")
            return

        telemetry_id = self._db.store_telemetry(telemetry)
        telemetry["_db_id"] = telemetry_id
        self.telemetry_received.emit(telemetry)
