from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFrame,
)


class ChatTab(QWidget):
    send_message_signal = pyqtSignal(str)
    clear_chat_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._bubbles: list[QLabel] = []   # track all bubble labels for resize
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Chat display area
        self.scroll = QScrollArea()
        self.scroll.setObjectName("ChatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_inner = QWidget()
        self.chat_inner.setObjectName("ChatContent")
        self.chat_layout = QVBoxLayout(self.chat_inner)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch(1)

        self.scroll.setWidget(self.chat_inner)
        layout.addWidget(self.scroll)

        # Thinking indicator
        self.thinking_label = QLabel("")
        self.thinking_label.setObjectName("ThinkingLabel")
        layout.addWidget(self.thinking_label)

        # Input area
        input_container = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask NEXUS-AI a technical question...")
        self.message_input.returnPressed.connect(self._on_send)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.setObjectName("SecondaryBtn")
        self.clear_btn.clicked.connect(self.clear_chat_signal.emit)
        self.clear_btn.clicked.connect(self.clear_display)

        input_container.addWidget(self.message_input)
        input_container.addWidget(self.send_btn)
        input_container.addWidget(self.clear_btn)
        layout.addLayout(input_container)

    def _bubble_max_width(self) -> int:
        """Return 75 % of the scroll viewport width, with a sensible fallback."""
        w = self.scroll.width()
        return int(w * 0.75) if w > 100 else 600

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Re-clamp all existing bubble max-widths when the panel is resized."""
        super().resizeEvent(event)
        max_w = self._bubble_max_width()
        for bubble in self._bubbles:
            bubble.setMaximumWidth(max_w)

    def _on_send(self) -> None:
        text = self.message_input.text().strip()
        if text:
            self.add_message(text, "user")
            self.send_message_signal.emit(text)
            self.message_input.clear()

    def add_message(self, text: str, sender: str) -> None:
        container = QFrame()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextFormat(Qt.TextFormat.MarkdownText)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setMaximumWidth(self._bubble_max_width())
        self._bubbles.append(bubble)

        if sender == "user":
            bubble.setObjectName("UserBubble")
            container_layout.addStretch(1)
            container_layout.addWidget(bubble)
        else:
            bubble.setObjectName("AiBubble")
            container_layout.addWidget(bubble)
            container_layout.addStretch(1)

        # Insert before the bottom stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, container)

        # Auto-scroll to bottom
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    def set_thinking(self, thinking: bool) -> None:
        if thinking:
            self.thinking_label.setText("NEXUS-AI is thinking...")
            self.send_btn.setEnabled(False)
            self.message_input.setEnabled(False)
        else:
            self.thinking_label.setText("")
            self.send_btn.setEnabled(True)
            self.message_input.setEnabled(True)

    def clear_display(self) -> None:
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._bubbles.clear()
