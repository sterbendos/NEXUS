from __future__ import annotations

import json

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class DashboardTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        status_group = QGroupBox("Hardware Status")
        status_layout = QFormLayout(status_group)
        self.serial_status = QLabel("Disconnected")
        self.serial_status.setProperty("status", "bad")
        self.tcp_status = QLabel("Disconnected")
        self.tcp_status.setProperty("status", "bad")
        status_layout.addRow("Serial:", self.serial_status)
        status_layout.addRow("TCP:", self.tcp_status)

        summary_group = QGroupBox("Network Environment Summary")
        summary_layout = QFormLayout(summary_group)
        self.total_events_label = QLabel("0")
        self.device_count_label = QLabel("0")
        self.last_device_label = QLabel("-")
        summary_layout.addRow("Telemetry Events:", self.total_events_label)
        summary_layout.addRow("Discovered Devices:", self.device_count_label)
        summary_layout.addRow("Last Device:", self.last_device_label)

        top_row = QHBoxLayout()
        top_row.addWidget(status_group, 1)
        top_row.addWidget(summary_group, 2)

        preview_group = QGroupBox("Live Telemetry Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Parsed telemetry lines will stream here once ingest starts.")
        preview_layout.addWidget(self.preview)

        activity_group = QGroupBox("Channel Activity")
        activity_layout = QVBoxLayout(activity_group)
        self.channel_activity = QPlainTextEdit()
        self.channel_activity.setReadOnly(True)
        self.channel_activity.setPlaceholderText("Connection and channel activity events will appear here.")
        activity_layout.addWidget(self.channel_activity)

        layout.addLayout(top_row)
        layout.addWidget(preview_group, 3)
        layout.addWidget(activity_group, 2)

    def update_connection(self, channel: str, connected: bool, message: str) -> None:
        target = self.serial_status if channel == "serial" else self.tcp_status
        target.setText(message)
        target.setProperty("status", "ok" if connected else "bad")
        target.style().polish(target)

    def append_telemetry_preview(self, telemetry: dict) -> None:
        line = json.dumps(telemetry, ensure_ascii=True)
        self.preview.appendPlainText(line)
        if self.preview.blockCount() > 300:
            text_lines = self.preview.toPlainText().splitlines()[-250:]
            self.preview.setPlainText("\n".join(text_lines))

    def append_channel_activity(self, message: str) -> None:
        self.channel_activity.appendPlainText(message)
        if self.channel_activity.blockCount() > 300:
            text_lines = self.channel_activity.toPlainText().splitlines()[-250:]
            self.channel_activity.setPlainText("\n".join(text_lines))

    def update_environment_summary(self, total_events: int, total_devices: int, last_device: str) -> None:
        self.total_events_label.setText(str(total_events))
        self.device_count_label.setText(str(total_devices))
        self.last_device_label.setText(last_device or "-")
