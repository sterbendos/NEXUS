from __future__ import annotations

import json
import select
import socket
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal, pyqtSlot

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
        self._write_lock = threading.Lock()

    def run(self) -> None:
        if serial is None:
            self.error.emit("pyserial is not installed; serial ingest is unavailable")
            self.status_changed.emit(False, "Serial unavailable")
            return

        port = self._port or HardwareInterfaceWrapper.auto_detect_serial_port()
        if not port:
            self.status_changed.emit(False, "No serial telemetry device detected")
            return

        if sys.platform.startswith("linux") and not port.startswith(("/dev/tty", "/dev/serial")):
            self.status_changed.emit(False, f"Invalid serial port: {port}")
            return
        elif sys.platform == "win32" and not port.upper().startswith("COM"):
            self.status_changed.emit(False, f"Invalid serial port: {port}")
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

    def send_line(self, line: str) -> bool:
        if self._serial_handle is None:
            return False
        with self._write_lock:
            try:
                self._serial_handle.write((line.rstrip("\r\n") + "\n").encode("utf-8"))
                self._serial_handle.flush()
                return True
            except OSError:
                return False


class TcpListenerThread(QThread):
    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, host: str = "0.0.0.0", port: int = 9000) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._running = False
        self._client_socket: socket.socket | None = None
        self._write_lock = threading.Lock()

    def run(self) -> None:
        self._running = True
        try:
            self._client_socket = socket.create_connection((self._host, self._port), timeout=10)
            self._client_socket.setblocking(False)
            self.status_changed.emit(True, f"TCP connected to {self._host}:{self._port}")

            buffer = b""
            while self._running and self._client_socket is not None:
                readable, _, exceptional = select.select([self._client_socket], [], [self._client_socket], 0.5)

                if self._client_socket in readable:
                    try:
                        data = self._client_socket.recv(4096)
                    except OSError as exc:
                        self.error.emit(f"TCP read error: {exc}")
                        break

                    if not data:
                        self.status_changed.emit(False, "TCP disconnected")
                        break

                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        text = line.decode("utf-8", errors="ignore").strip()
                        if text:
                            self.line_received.emit(text)

                if self._client_socket in exceptional:
                    self.error.emit("TCP socket error")
                    break

        except OSError as exc:
            self.error.emit(f"TCP connection failed: {exc}")
        finally:
            if self._client_socket is not None:
                try:
                    self._client_socket.close()
                except OSError:
                    pass
                self._client_socket = None
            self.status_changed.emit(False, "TCP stopped")
            self._running = False

    def stop(self) -> None:
        self._running = False
        if self._client_socket is not None:
            try:
                self._client_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._client_socket.close()
            except OSError:
                pass
        self.wait(1500)

    def send_line(self, line: str) -> bool:
        if self._client_socket is None:
            return False
        with self._write_lock:
            try:
                self._client_socket.sendall((line.rstrip("\r\n") + "\n").encode("utf-8"))
                return True
            except OSError:
                return False


class DbWriter(QObject):
    """Writes telemetry to database in a background thread."""
    write_complete = pyqtSignal(dict, int)
    write_error = pyqtSignal(str)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._db = database

    @pyqtSlot(dict)
    def handle_telemetry(self, telemetry: dict[str, Any]) -> None:
        try:
            telemetry_id = self._db.store_telemetry(telemetry)
            telemetry["_db_id"] = telemetry_id
            self.write_complete.emit(telemetry, telemetry_id)
        except Exception as exc:
            self.write_error.emit(f"DB write failed: {exc}")


class TelemetryIngestManager(QObject):
    raw_line_received = pyqtSignal(str)
    telemetry_received = pyqtSignal(dict)
    telemetry_to_write = pyqtSignal(dict)
    telemetry_invalid = pyqtSignal(str)
    connection_state = pyqtSignal(str, bool, str)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._db = database
        self._validator = TelemetrySchemaValidator()
        self._serial_thread: SerialListenerThread | None = None
        self._tcp_thread: TcpListenerThread | None = None
        self._db_writer_thread: QThread | None = None
        self._db_writer: DbWriter | None = None
        self._rate_limits: dict[str, float] = defaultdict(float)
        self._MAX_RATE_PER_SEC = 100
        self._start_db_writer()

    def _check_rate_limit(self, source: str) -> bool:
        now = time.monotonic()
        min_interval = 1.0 / self._MAX_RATE_PER_SEC
        if now - self._rate_limits[source] < min_interval:
            return False
        self._rate_limits[source] = now
        return True

    def _start_db_writer(self) -> None:
        self._db_writer_thread = QThread()
        self._db_writer = DbWriter(self._db)
        self._db_writer.moveToThread(self._db_writer_thread)
        self.telemetry_to_write.connect(
            self._db_writer.handle_telemetry,
            Qt.ConnectionType.QueuedConnection,
        )
        # Route write_complete back to main thread for signal emission
        self._db_writer.write_complete.connect(self._on_write_complete, Qt.ConnectionType.QueuedConnection)
        self._db_writer.write_error.connect(self._on_db_write_error, Qt.ConnectionType.QueuedConnection)
        self._db_writer_thread.start()

    def _on_write_complete(self, telemetry: dict[str, Any], telemetry_id: int) -> None:
        self.telemetry_received.emit(telemetry)

    def _on_db_write_error(self, message: str) -> None:
        self.telemetry_invalid.emit(message)

    def stop_db_writer(self) -> None:
        if self._db_writer_thread is not None:
            self._db_writer_thread.quit()
            self._db_writer_thread.wait(2000)
            self._db_writer_thread = None
            self._db_writer = None

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
            self.connection_state.emit("tcp", True, "TCP session already running")
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
        self.stop_db_writer()

    def send_serial_command(self, line: str) -> bool:
        if self._serial_thread and self._serial_thread.isRunning():
            return self._serial_thread.send_line(line)
        return False

    def has_serial_command_channel(self) -> bool:
        return bool(self._serial_thread and self._serial_thread.isRunning())

    def send_tcp_command(self, line: str) -> bool:
        if self._tcp_thread and self._tcp_thread.isRunning():
            return self._tcp_thread.send_line(line)
        return False

    def has_tcp_command_channel(self) -> bool:
        return bool(self._tcp_thread and self._tcp_thread.isRunning())

    def send_command(self, line: str) -> bool:
        if self.has_tcp_command_channel():
            return self.send_tcp_command(line)
        if self.has_serial_command_channel():
            return self.send_serial_command(line)
        return False

    def _handle_line(self, source: str, line: str) -> None:
        if not self._check_rate_limit(source):
            return
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

        # Write to DB in background thread via DbWriter
        if self._db_writer is not None:
            self.telemetry_to_write.emit(telemetry)
        else:
            try:
                telemetry_id = self._db.store_telemetry(telemetry)
            except Exception as exc:
                self.telemetry_invalid.emit(f"DB write failed: {exc}")
                return
            telemetry["_db_id"] = telemetry_id
            self._on_write_complete(telemetry, telemetry_id)
