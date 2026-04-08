from __future__ import annotations

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QPushButton, QStackedWidget, QWidget


class NavigationController(QObject):
    def __init__(self, stack: QStackedWidget) -> None:
        super().__init__()
        self._stack = stack
        self._buttons: dict[int, QPushButton] = {}

    def add_page(self, page: QWidget, button: QPushButton) -> int:
        index = self._stack.addWidget(page)
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False, i=index: self.set_current(i))
        self._buttons[index] = button

        if self._stack.count() == 1:
            self.set_current(index)
        return index

    def set_current(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for entry_index, button in self._buttons.items():
            button.setChecked(entry_index == index)
