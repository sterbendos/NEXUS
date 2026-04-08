from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class NetworkMonitorTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        summary_group = QGroupBox("Traffic Summary")
        summary_layout = QFormLayout(summary_group)
        self.total_devices = QLabel("0")
        self.total_events = QLabel("0")
        self.http_meta = QLabel("HTTP metadata placeholder")
        summary_layout.addRow("Discovered Devices:", self.total_devices)
        summary_layout.addRow("Telemetry Events:", self.total_events)
        summary_layout.addRow("HTTP Metadata:", self.http_meta)

        table_group = QGroupBox("IP / Device Discovery")
        table_layout = QVBoxLayout(table_group)
        self.device_table = QTableWidget(0, 5)
        self.device_table.setHorizontalHeaderLabels(["Device ID", "IP", "MAC", "Last Seen", "Events"])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.device_table.setAlternatingRowColors(True)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.device_table)

        layout.addWidget(summary_group)
        layout.addWidget(table_group, 1)

    def update_devices(self, devices: list[dict]) -> None:
        self.device_table.setRowCount(len(devices))
        total_events = 0

        for row_index, device in enumerate(devices):
            total_events += int(device.get("events", 0))
            values = [
                str(device.get("device_id", "")),
                str(device.get("ip", "")),
                str(device.get("mac", "")),
                str(device.get("last_seen", "")),
                str(device.get("events", 0)),
            ]
            for col_index, value in enumerate(values):
                self.device_table.setItem(row_index, col_index, QTableWidgetItem(value))

        self.total_devices.setText(str(len(devices)))
        self.total_events.setText(str(total_events))
