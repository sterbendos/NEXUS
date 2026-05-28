from __future__ import annotations

import json
import requests
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal


class ChatWorker(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, base_url: str, model: str, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.messages = messages

    def run(self) -> None:
        try:
            body = {
                "model": self.model,
                "messages": self.messages,
                "stream": False,
                "options": {"temperature": 0.5},
            }

            response = requests.post(f"{self.base_url}/api/chat", json=body, timeout=60)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Ollama response is not a JSON object")

            # Extract content from the chat response format
            message_content = data.get("message", {}).get("content", "")
            self.finished_signal.emit(message_content)

        except requests.exceptions.RequestException as e:
            self.error_signal.emit(f"Ollama chat failed: {e}")
        except (json.JSONDecodeError, ValueError) as e:
            self.error_signal.emit(f"Invalid Ollama response: {e}")
        except Exception as e:
            self.error_signal.emit(f"Unexpected error during chat: {e}")


class ChatConnector(QObject):
    """Manages conversational state and async communication with Ollama."""

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
                           "You helping penetration testers, ethical hackers, and incident response officers."
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

        self._worker = ChatWorker(self.base_url, self.model, self.history)
        self._worker.setParent(self) # Hard life-cycle lock
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.error_signal.connect(self._on_worker_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_worker_finished(self, response_text: str) -> None:
        # Add assistant response to history
        self.history.append({"role": "assistant", "content": response_text})
        self.message_received.emit(response_text)
        self._worker = None

    def _on_worker_error(self, message: str) -> None:
        # Optionally remove the failed user message if you want to retry cleanly
        # self.history.pop() 
        self.error_occurred.emit(message)
        self._worker = None

    def clear_history(self) -> None:
        system_msg = self.history[0] if self.history else None
        self.history = []
        if system_msg:
            self.history.append(system_msg)
