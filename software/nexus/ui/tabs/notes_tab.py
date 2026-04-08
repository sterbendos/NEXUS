from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class NotesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(12)

        controls_group = QGroupBox("Event-Linked Notes")
        controls_layout = QFormLayout(controls_group)
        self.event_id_input = QLineEdit()
        self.timestamp_label = QLabel(self._now())
        button_row = QHBoxLayout()
        self.save_note_btn = QPushButton("Save Note")
        self.export_md_btn = QPushButton("Export Markdown")
        self.export_pdf_btn = QPushButton("Export PDF")
        button_row.addWidget(self.save_note_btn)
        button_row.addWidget(self.export_md_btn)
        button_row.addWidget(self.export_pdf_btn)
        self.status_label = QLabel("Ready")
        controls_layout.addRow("Event ID:", self.event_id_input)
        controls_layout.addRow("Timestamp:", self.timestamp_label)
        controls_layout.addRow(button_row)
        controls_layout.addRow(self.status_label)

        editor_group = QGroupBox("Markdown Editor")
        editor_layout = QVBoxLayout(editor_group)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Write incident notes in Markdown...")
        editor_layout.addWidget(self.editor)

        history_group = QGroupBox("Recent Timestamped Entries")
        history_layout = QVBoxLayout(history_group)
        self.notes_table = QTableWidget(0, 4)
        self.notes_table.setHorizontalHeaderLabels(["ID", "Event ID", "Timestamp", "Preview"])
        self.notes_table.horizontalHeader().setStretchLastSection(True)
        self.notes_table.setAlternatingRowColors(True)
        self.notes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.notes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self.notes_table)

        layout.addWidget(controls_group)
        layout.addWidget(editor_group, 2)
        layout.addWidget(history_group, 1)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def refresh_timestamp(self) -> None:
        self.timestamp_label.setText(self._now())

    def markdown(self) -> str:
        return self.editor.toMarkdown()

    def set_status(self, message: str, ok: bool = True) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("status", "ok" if ok else "bad")
        self.status_label.style().polish(self.status_label)

    def populate_notes(self, notes: list[dict]) -> None:
        self.notes_table.setRowCount(len(notes))
        for row_index, note in enumerate(notes):
            preview = str(note.get("content", "")).replace("\n", " ")[:90]
            values = [
                str(note.get("id", "")),
                str(note.get("event_id", "")),
                str(note.get("timestamp", "")),
                preview,
            ]
            for col_index, value in enumerate(values):
                self.notes_table.setItem(row_index, col_index, QTableWidgetItem(value))
