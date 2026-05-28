from __future__ import annotations

import json

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor
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
        self._event_tick_count = 0          # events received in current second
        self._chart_data: list[float] = [0.0] * 60  # 60-second rolling window
        self._series = None
        self._y_axis = None
        self._chart_timer: QTimer | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        # --- Hardware Status ---
        status_group = QGroupBox("Hardware Status")
        status_layout = QFormLayout(status_group)
        self.serial_status = QLabel("Disconnected")
        self.serial_status.setProperty("status", "bad")
        self.tcp_status = QLabel("Disconnected")
        self.tcp_status.setProperty("status", "bad")
        status_layout.addRow("Serial:", self.serial_status)
        status_layout.addRow("TCP:", self.tcp_status)

        # --- Environment Summary ---
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

        # --- Live Telemetry Preview ---
        preview_group = QGroupBox("Live Telemetry Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Parsed telemetry lines will stream here once ingest starts.")
        preview_layout.addWidget(self.preview)

        # --- Channel Activity ---
        activity_group = QGroupBox("Channel Activity")
        activity_layout = QVBoxLayout(activity_group)
        self.channel_activity = QPlainTextEdit()
        self.channel_activity.setReadOnly(True)
        self.channel_activity.setPlaceholderText("Connection and channel activity events will appear here.")
        activity_layout.addWidget(self.channel_activity)

        layout.addLayout(top_row)
        layout.addWidget(preview_group, 3)
        layout.addWidget(activity_group, 2)

        # --- Events/sec Sparkline (optional PyQt6-Charts) ---
        self._try_build_chart(layout)

    def _try_build_chart(self, parent_layout: QVBoxLayout) -> None:
        """Build a QChart sparkline if PyQt6-Charts is available; silently skip if not."""
        try:
            from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QColor, QPen

            chart_group = QGroupBox("Events / Second — last 60 s")
            chart_layout = QVBoxLayout(chart_group)

            self._series = QLineSeries()
            pen = QPen(QColor("#79d5ff"))
            pen.setWidth(2)
            self._series.setPen(pen)
            for i, v in enumerate(self._chart_data):
                self._series.append(float(i), v)

            chart = QChart()
            chart.addSeries(self._series)
            chart.setBackgroundBrush(QColor("#0f1d2b"))
            chart.setPlotAreaBackgroundBrush(QColor("#101d2b"))
            chart.setPlotAreaBackgroundVisible(True)
            chart.legend().hide()

            # Margins: use QMargins directly
            from PyQt6.QtCore import QMargins
            chart.setMargins(QMargins(4, 4, 4, 4))

            x_axis = QValueAxis()
            x_axis.setRange(0, 59)
            x_axis.setLabelsVisible(False)
            x_axis.setGridLineColor(QColor("#1f3448"))
            chart.addAxis(x_axis, Qt.AlignmentFlag.AlignBottom)
            self._series.attachAxis(x_axis)

            self._y_axis = QValueAxis()
            self._y_axis.setRange(0, 10)
            self._y_axis.setLabelsColor(QColor("#9ab4cd"))
            self._y_axis.setGridLineColor(QColor("#1f3448"))
            self._y_axis.setTickCount(4)
            chart.addAxis(self._y_axis, Qt.AlignmentFlag.AlignLeft)
            self._series.attachAxis(self._y_axis)

            chart_view = QChartView(chart)
            chart_view.setFixedHeight(130)
            chart_layout.addWidget(chart_view)
            parent_layout.addWidget(chart_group)

            # Tick every second
            self._chart_timer = QTimer(self)
            self._chart_timer.timeout.connect(self._tick_chart)
            self._chart_timer.start(1000)

        except Exception:
            # PyQt6-Charts not installed — no chart, no crash
            pass

    def _tick_chart(self) -> None:
        """Rotate rolling window and redraw series once per second."""
        self._chart_data.append(float(self._event_tick_count))
        self._chart_data = self._chart_data[-60:]
        self._event_tick_count = 0

        if self._series is None or self._y_axis is None:
            return

        self._series.clear()
        for i, v in enumerate(self._chart_data):
            self._series.append(float(i), v)

        peak = max(self._chart_data) if self._chart_data else 1.0
        self._y_axis.setRange(0, max(peak * 1.25, 5.0))

    # ------------------------------------------------------------------
    # Public API used by AppController
    # ------------------------------------------------------------------

    def update_connection(self, channel: str, connected: bool, message: str) -> None:
        target = self.serial_status if channel == "serial" else self.tcp_status
        target.setText(message)
        target.setProperty("status", "ok" if connected else "bad")
        target.style().polish(target)

    def append_telemetry_preview(self, telemetry: dict) -> None:
        """Append a parsed telemetry line; count it for the chart tick."""
        self._event_tick_count += 1
        line = json.dumps(telemetry, ensure_ascii=True)
        self.preview.appendPlainText(line)
        # Efficient trim: remove first 50 blocks instead of full setText
        if self.preview.blockCount() > 300:
            cursor = self.preview.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down,
                                QTextCursor.MoveMode.KeepAnchor, 50)
            cursor.removeSelectedText()

    def append_channel_activity(self, message: str) -> None:
        self.channel_activity.appendPlainText(message)
        if self.channel_activity.blockCount() > 300:
            cursor = self.channel_activity.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down,
                                QTextCursor.MoveMode.KeepAnchor, 50)
            cursor.removeSelectedText()

    def update_environment_summary(self, total_events: int, total_devices: int, last_device: str) -> None:
        self.total_events_label.setText(str(total_events))
        self.device_count_label.setText(str(total_devices))
        self.last_device_label.setText(last_device or "-")
