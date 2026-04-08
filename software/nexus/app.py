from __future__ import annotations

from nexus.ai.ai_connector import AIConnector
from nexus.ai.chat_connector import ChatConnector
from nexus.config import DB_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL
from nexus.controllers.app_controller import AppController
from nexus.db.database import DatabaseManager
from nexus.hardware.telemetry_ingest import TelemetryIngestManager
from nexus.notes.notes_service import NotesService
from nexus.ui.main_window import MainWindow


def create_app() -> MainWindow:
    database = DatabaseManager(DB_PATH)
    ingest = TelemetryIngestManager(database)
    ai_connector = AIConnector(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    chat_connector = ChatConnector(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    notes_service = NotesService(database)

    window = MainWindow()
    controller = AppController(
        window=window,
        database=database,
        ingest=ingest,
        ai_connector=ai_connector,
        chat_connector=chat_connector,
        notes_service=notes_service,
    )

    window.on_close = controller.shutdown
    window.controller = controller  # keep references alive
    return window
