from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter

from nexus.db.database import DatabaseManager


class NotesService:
    def __init__(self, database: DatabaseManager) -> None:
        self._db = database

    def save_note(self, event_id: str, markdown_content: str) -> int:
        return self._db.store_note(event_id=event_id.strip(), content=markdown_content)

    def recent_notes(self, limit: int = 100) -> list[dict]:
        return self._db.fetch_notes(limit=limit)

    @staticmethod
    def export_markdown(file_path: str | Path, markdown_content: str) -> None:
        Path(file_path).write_text(markdown_content, encoding="utf-8")

    @staticmethod
    def export_pdf(file_path: str | Path, markdown_content: str, title: str = "NEXUS Notes") -> None:
        document = QTextDocument()
        document.setMarkdown(markdown_content)
        document.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, title)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(str(file_path))
        document.print(printer)
