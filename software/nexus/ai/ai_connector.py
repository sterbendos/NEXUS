from __future__ import annotations

import json
from typing import Any

import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from nexus.ai.prompt_formatter import PromptFormatter
from nexus.ai.response_parser import ResponseParser


class OllamaWorker(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, base_url: str, model: str, log_payload: dict[str, Any]) -> None:
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.log_payload = log_payload
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        try:
            prompt = PromptFormatter.build_prompt(self.log_payload)
            body = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1},
            }

            response = requests.post(f"{self.base_url}/api/generate", json=body, timeout=60)
            if self._cancel_requested:
                return

            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Ollama response is not a JSON object")

            parsed = ResponseParser.parse(data)
            if self._cancel_requested:
                return

            self.finished_signal.emit(parsed)

        except requests.exceptions.RequestException as exc:
            self.error_signal.emit(f"Ollama request failed: {exc}")
        except (json.JSONDecodeError, ValueError) as exc:
            self.error_signal.emit(f"Invalid Ollama response: {exc}")
        except Exception as exc:
            self.error_signal.emit(f"Unexpected error during analysis: {exc}")


class AIConnector(QObject):
    """Asynchronous connector for local Ollama API via background thread."""

    analysis_ready = pyqtSignal(dict)
    analysis_error = pyqtSignal(str)
    analysis_started = pyqtSignal()

    def __init__(self, base_url: str, model: str) -> None:
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._worker: OllamaWorker | None = None

    def analyze(self, log_payload: dict[str, Any]) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.analysis_error.emit("An analysis is already in progress.")
            return

        self.analysis_started.emit()

        self._worker = OllamaWorker(self.base_url, self.model, log_payload)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.error_signal.connect(self._on_worker_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_worker_finished(self, result: dict[str, Any]) -> None:
        self.analysis_ready.emit(result)
        self._worker = None

    def _on_worker_error(self, message: str) -> None:
        self.analysis_error.emit(message)
        self._worker = None

    def cancel(self) -> None:
        """Request cancellation without force-terminating the worker thread."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_cancel()
            self.analysis_error.emit("Analysis cancellation requested.")
