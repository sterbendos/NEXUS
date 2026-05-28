from __future__ import annotations

import json

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AIAnalysisTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._elapsed_seconds = 0
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)
        self._build_ui()

    def _tick_elapsed(self) -> None:
        self._elapsed_seconds += 1
        self.status_label.setText(f"Running analysis... {self._elapsed_seconds}s")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        input_group = QGroupBox("Structured Input")
        input_layout = QVBoxLayout(input_group)
        self.input_view = QPlainTextEdit()
        self.input_view.setPlaceholderText("Paste telemetry JSON or leave blank to analyze last ingested event")

        btn_row = QHBoxLayout()
        self.analyze_btn = QPushButton("Run AI Analysis")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("CancelBtn")
        self.cancel_btn.setEnabled(False)
        btn_row.addWidget(self.analyze_btn)
        btn_row.addWidget(self.cancel_btn)

        self.status_label = QLabel("Idle")
        self.status_label.setProperty("status", "warn")

        input_layout.addWidget(self.input_view)
        input_layout.addLayout(btn_row)
        input_layout.addWidget(self.status_label)

        output_group = QGroupBox("AI Output")
        output_layout = QFormLayout(output_group)
        self.classification_output = QLineEdit()
        self.classification_output.setReadOnly(True)
        self.severity_output = QLineEdit()
        self.severity_output.setReadOnly(True)
        self.mitigation_output = QPlainTextEdit()
        self.mitigation_output.setReadOnly(True)
        self.rationale_output = QPlainTextEdit()
        self.rationale_output.setReadOnly(True)
        self.hardware_jobs_output = QPlainTextEdit()
        self.hardware_jobs_output.setReadOnly(True)
        self.dispatch_jobs_btn = QPushButton("Dispatch Hardware Jobs")
        self.dispatch_jobs_btn.setEnabled(False)
        output_layout.addRow("Threat Classification:", self.classification_output)
        output_layout.addRow("Severity:", self.severity_output)
        output_layout.addRow("Suggested Mitigation:", self.mitigation_output)
        output_layout.addRow("Rationale:", self.rationale_output)
        output_layout.addRow("Hardware Jobs:", self.hardware_jobs_output)
        output_layout.addRow(self.dispatch_jobs_btn)

        layout.addWidget(input_group, 1)
        layout.addWidget(output_group, 1)

    def set_status(self, text: str, state: str = "warn") -> None:
        if state == "warn" and "Running" in text:
            self._elapsed_seconds = 0
            self._elapsed_timer.start(1000)
            self.analyze_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
        else:
            self._elapsed_timer.stop()
            self.analyze_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

        self.status_label.setText(text)
        self.status_label.setProperty("status", state)
        self.status_label.style().polish(self.status_label)

    def set_result(self, result: dict) -> None:
        self.classification_output.setText(str(result.get("threat_classification", "Unknown")))
        self.severity_output.setText(str(result.get("severity", "medium")))
        self.mitigation_output.setPlainText(str(result.get("suggested_mitigation", "")))
        self.rationale_output.setPlainText(str(result.get("rationale", "")))
        jobs = result.get("hardware_jobs") or []
        if jobs:
            self.hardware_jobs_output.setPlainText(json.dumps(jobs, ensure_ascii=True, indent=2))
            self.dispatch_jobs_btn.setEnabled(True)
        else:
            self.hardware_jobs_output.setPlainText("No hardware jobs proposed.")
            self.dispatch_jobs_btn.setEnabled(False)
