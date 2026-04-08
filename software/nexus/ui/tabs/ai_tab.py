from __future__ import annotations

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
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        input_group = QGroupBox("Structured Input")
        input_layout = QVBoxLayout(input_group)
        self.input_view = QPlainTextEdit()
        self.input_view.setPlaceholderText("Paste telemetry JSON or leave blank to analyze last ingested event")
        self.analyze_btn = QPushButton("Run AI Analysis")
        self.status_label = QLabel("Idle")
        self.status_label.setProperty("status", "warn")
        input_layout.addWidget(self.input_view)
        input_layout.addWidget(self.analyze_btn)
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
        output_layout.addRow("Threat Classification:", self.classification_output)
        output_layout.addRow("Severity:", self.severity_output)
        output_layout.addRow("Suggested Mitigation:", self.mitigation_output)
        output_layout.addRow("Rationale:", self.rationale_output)

        layout.addWidget(input_group, 1)
        layout.addWidget(output_group, 1)

    def set_status(self, text: str, state: str = "warn") -> None:
        self.status_label.setText(text)
        self.status_label.setProperty("status", state)
        self.status_label.style().polish(self.status_label)

    def set_result(self, result: dict) -> None:
        self.classification_output.setText(str(result.get("threat_classification", "Unknown")))
        self.severity_output.setText(str(result.get("severity", "medium")))
        self.mitigation_output.setPlainText(str(result.get("suggested_mitigation", "")))
        self.rationale_output.setPlainText(str(result.get("rationale", "")))
