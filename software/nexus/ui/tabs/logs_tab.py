from __future__ import annotations

import csv
import json

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LogsDatabaseTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._current_rows: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        filters_group = QGroupBox("Queryable Logs")
        filters_layout = QFormLayout(filters_group)
        self.device_filter_input = QLineEdit()
        self.device_filter_input.setPlaceholderText("device_id filter (optional)")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 1000)
        self.limit_spin.setValue(200)

        filter_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Run Query")
        self.export_csv_btn = QPushButton("Export CSV")
        self.purge_btn = QPushButton("Purge Old Rows...")
        self.status_label = QLabel("Ready")
        filter_row.addWidget(self.refresh_btn)
        filter_row.addWidget(self.export_csv_btn)
        filter_row.addWidget(self.purge_btn)
        filter_row.addWidget(self.status_label)

        filters_layout.addRow("Device Filter:", self.device_filter_input)
        filters_layout.addRow("Limit:", self.limit_spin)
        filters_layout.addRow(filter_row)

        table_group = QGroupBox("Telemetry Logs")
        table_layout = QVBoxLayout(table_group)
        self.logs_table = QTableWidget(0, 6)
        self.logs_table.setHorizontalHeaderLabels(
            ["ID", "Timestamp", "Device", "Source", "Channel", "Payload Preview"]
        )
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.logs_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.logs_table)

        layout.addWidget(filters_group)
        layout.addWidget(table_group, 1)

    def set_status(self, message: str, ok: bool = True) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("status", "ok" if ok else "bad")
        self.status_label.style().polish(self.status_label)

    def populate_logs(self, logs: list[dict]) -> None:
        self._current_rows = logs
        self.logs_table.setRowCount(len(logs))
        for row_index, row in enumerate(logs):
            payload_preview = json.dumps(row.get("payload", {}), ensure_ascii=True)[:120]
            values = [
                str(row.get("id", "")),
                str(row.get("timestamp", "")),
                str(row.get("device_id", "")),
                str(row.get("source", "")),
                str(row.get("channel", "")),
                payload_preview,
            ]
            for col_index, value in enumerate(values):
                self.logs_table.setItem(row_index, col_index, QTableWidgetItem(value))

    def export_to_csv(self, path: str) -> None:
        """Write the currently displayed rows to a CSV file."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Device", "Source", "Channel", "Payload"])
            for row in self._current_rows:
                writer.writerow(
                    [
                        row.get("id", ""),
                        row.get("timestamp", ""),
                        row.get("device_id", ""),
                        row.get("source", ""),
                        row.get("channel", ""),
                        json.dumps(row.get("payload", {}), ensure_ascii=True),
                    ]
                )
