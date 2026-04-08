from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from nexus.app import create_app
from nexus.config import APP_NAME


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
