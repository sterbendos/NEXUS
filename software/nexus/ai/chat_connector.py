from __future__ import annotations

import json
from typing import Any

import requests as requests_lib
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class ChatWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, base_url: str, model: str, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.messages = messages
        self._session = requests_lib.Session()

    def run(self) -> None:
        try:
            body = {
                "model": self.model,
                "messages": self.messages,
                "stream": False,
                "options": {"temperature": 0.5},
            }

            response = self._session.post(
                f"{self.base_url}/api/chat", json=body, timeout=(3.05, 10)
            )
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Ollama response is not a JSON object")

            message = data.get("message")
            if not isinstance(message, dict):
                raise ValueError("Ollama response is missing a message object")

            message_content = str(message.get("content", ""))
            self.finished_signal.emit(message_content)

        except requests_lib.exceptions.RequestException as e:
            self.error_signal.emit(f"Ollama chat failed: {e}")
        except (json.JSONDecodeError, ValueError) as e:
            self.error_signal.emit(f"Invalid Ollama response: {e}")
        except Exception as e:
            self.error_signal.emit(f"Unexpected error during chat: {e}")
        finally:
            self._session.close()


class ChatConnector(QObject):
    """Manages conversational state and async communication with Ollama."""

    MAX_HISTORY_LENGTH = 20

    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    thinking_started = pyqtSignal()

    def __init__(self, base_url: str, model: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.history: list[dict[str, str]] = [
            {
                "role": "system",
                "content": "You are NEXUS-AI, an expert cybersecurity assistant. You provide technical, precise information. "
                           "You help penetration testers, ethical hackers, and incident response officers."
            }
        ]
        self._worker: ChatWorker | None = None

    def send_message(self, text: str) -> None:
        if self._worker is not None and self._worker.isRunning():
            self.error_occurred.emit("AI is currently thinking...")
            return

        # Add user message to history
        self.history.append({"role": "user", "content": text})
        self.thinking_started.emit()

        history_snapshot = [dict(message) for message in self.history]
        self._worker = ChatWorker(self.base_url, self.model, history_snapshot)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.error_signal.connect(self._on_worker_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_worker_finished(self, response_text: str) -> None:
        self.history.append({"role": "assistant", "content": response_text})
        # Trim history to prevent unbounded growth
        if len(self.history) > self.MAX_HISTORY_LENGTH * 2 + 1:
            system = self.history[:1]
            recent = self.history[-(self.MAX_HISTORY_LENGTH * 2):]
            self.history = system + recent
        self.message_received.emit(response_text)
        self._worker = None

    def _on_worker_error(self, message: str) -> None:
        if self.history and self.history[-1]["role"] == "user":
            self.history.pop()
        self.error_occurred.emit(message)
        self._worker = None

    def clear_history(self) -> None:
        system_msg = self.history[0] if self.history else None
        self.history = []
        if system_msg:
            self.history.append(system_msg)
