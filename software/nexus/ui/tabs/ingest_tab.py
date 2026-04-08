from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class DataIngestTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        controls = QHBoxLayout()

        serial_group = QGroupBox("Serial (USB) Listener")
        serial_layout = QFormLayout(serial_group)
        self.serial_port_input = QLineEdit()
        self.serial_port_input.setPlaceholderText("Auto detect")
        self.serial_baud_input = QLineEdit("115200")
        self.serial_start_btn = QPushButton("Start Serial")
        self.serial_stop_btn = QPushButton("Stop Serial")
        serial_buttons = QHBoxLayout()
        serial_buttons.addWidget(self.serial_start_btn)
        serial_buttons.addWidget(self.serial_stop_btn)
        serial_layout.addRow("Port:", self.serial_port_input)
        serial_layout.addRow("Baud:", self.serial_baud_input)
        serial_layout.addRow(serial_buttons)

        tcp_group = QGroupBox("TCP Socket Listener")
        tcp_layout = QFormLayout(tcp_group)
        self.tcp_host_input = QLineEdit("0.0.0.0")
        self.tcp_port_input = QLineEdit("9000")
        self.tcp_start_btn = QPushButton("Start TCP")
        self.tcp_stop_btn = QPushButton("Stop TCP")
        tcp_buttons = QHBoxLayout()
        tcp_buttons.addWidget(self.tcp_start_btn)
        tcp_buttons.addWidget(self.tcp_stop_btn)
        tcp_layout.addRow("Host:", self.tcp_host_input)
        tcp_layout.addRow("Port:", self.tcp_port_input)
        tcp_layout.addRow(tcp_buttons)

        controls.addWidget(serial_group)
        controls.addWidget(tcp_group)

        self.status_label = QLabel("Idle")
        self.status_label.setProperty("status", "warn")

        viewer_split = QSplitter()

        raw_group = QGroupBox("Raw Feed Viewer")
        raw_layout = QVBoxLayout(raw_group)
        self.raw_view = QPlainTextEdit()
        self.raw_view.setReadOnly(True)
        self.raw_view.setPlaceholderText("Raw serial/TCP frames will appear here.")
        raw_layout.addWidget(self.raw_view)

        parsed_group = QGroupBox("Parsed JSON Telemetry")
        parsed_layout = QVBoxLayout(parsed_group)
        self.parsed_view = QPlainTextEdit()
        self.parsed_view.setReadOnly(True)
        self.parsed_view.setPlaceholderText("Latest validated telemetry JSON.")
        parsed_layout.addWidget(self.parsed_view)

        viewer_split.addWidget(raw_group)
        viewer_split.addWidget(parsed_group)
        viewer_split.setStretchFactor(0, 1)
        viewer_split.setStretchFactor(1, 1)

        layout.addLayout(controls)
        layout.addWidget(self.status_label)
        layout.addWidget(viewer_split, 1)

    def append_raw_line(self, line: str) -> None:
        self.raw_view.appendPlainText(line)
        if self.raw_view.blockCount() > 800:
            lines = self.raw_view.toPlainText().splitlines()[-600:]
            self.raw_view.setPlainText("\n".join(lines))

    def show_parsed(self, telemetry: dict) -> None:
        text = json.dumps(telemetry, ensure_ascii=True, indent=2)
        self.parsed_view.setPlainText(text)

    def set_status(self, message: str, ok: bool | None = None) -> None:
        self.status_label.setText(message)
        if ok is None:
            tag = "warn"
        else:
            tag = "ok" if ok else "bad"
        self.status_label.setProperty("status", tag)
        self.status_label.style().polish(self.status_label)
