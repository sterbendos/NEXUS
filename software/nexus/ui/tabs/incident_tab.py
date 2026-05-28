from __future__ import annotations

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class IncidentResponseTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        top_row = QHBoxLayout()

        timeline_group = QGroupBox("Event Timeline")
        timeline_layout = QVBoxLayout(timeline_group)
        self.timeline = QListWidget()
        self.timeline.setAlternatingRowColors(True)
        timeline_layout.addWidget(self.timeline)

        anomaly_group = QGroupBox("Anomaly Logs")
        anomaly_layout = QVBoxLayout(anomaly_group)
        self.anomaly_logs = QPlainTextEdit()
        self.anomaly_logs.setReadOnly(True)
        self.anomaly_logs.setPlaceholderText("Ingest validation failures and anomaly records are listed here.")
        anomaly_layout.addWidget(self.anomaly_logs)

        top_row.addWidget(timeline_group, 1)
        top_row.addWidget(anomaly_group, 1)

        placeholder_group = QGroupBox("Environment Change Detection")
        placeholder_layout = QVBoxLayout(placeholder_group)
        self.change_detection_label = QLabel(
            "Placeholder: baseline diff and drift detection pipeline hooks will render here."
        )
        self.change_detection_label.setWordWrap(True)
        placeholder_layout.addWidget(self.change_detection_label)

        layout.addLayout(top_row, 1)
        layout.addWidget(placeholder_group)

    def add_timeline_event(self, text: str) -> None:
        self.timeline.insertItem(0, text)
        if self.timeline.count() > 500:
            self.timeline.takeItem(self.timeline.count() - 1)

    def add_anomaly(self, text: str) -> None:
        self.anomaly_logs.appendPlainText(text)
        if self.anomaly_logs.blockCount() > 600:
            cursor = self.anomaly_logs.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor, 100)
            cursor.removeSelectedText()
            self.anomaly_logs.setTextCursor(cursor)
