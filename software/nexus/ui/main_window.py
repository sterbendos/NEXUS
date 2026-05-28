from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nexus.controllers.navigation_controller import NavigationController
from nexus.ui.styles import DARK_THEME_STYLESHEET
from nexus.ui.tabs.ai_tab import AIAnalysisTab
from nexus.ui.tabs.chat_tab import ChatTab
from nexus.ui.tabs.dashboard_tab import DashboardTab
from nexus.ui.tabs.incident_tab import IncidentResponseTab
from nexus.ui.tabs.ingest_tab import DataIngestTab
from nexus.ui.tabs.logs_tab import LogsDatabaseTab
from nexus.ui.tabs.network_tab import NetworkMonitorTab
from nexus.ui.tabs.notes_tab import NotesTab
from nexus.ui.tabs.pentest_tab import PentestingTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.on_close = None
        self._section_meta: list[tuple[str, str]] = []
        self.setWindowTitle("NEXUS - Intelligent Network Environment Analysis")
        self.resize(1480, 900)
        self._build_ui()
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        self._init_status_bar()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(258)

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(14, 14, 14, 14)
        side_layout.setSpacing(8)

        brand_card = QFrame()
        brand_card.setObjectName("BrandCard")
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(10, 10, 10, 10)
        brand_layout.setSpacing(4)

        title = QLabel("NEXUS")
        title.setObjectName("BrandTitle")
        subtitle = QLabel("Intelligent Network Environment Analysis")
        subtitle.setObjectName("BrandSub")
        subtitle.setWordWrap(True)
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        side_layout.addWidget(brand_card)

        hint = QLabel("Navigation")
        hint.setObjectName("SidebarHint")
        side_layout.addWidget(hint)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")
        self.nav = NavigationController(self.stack)

        self.dashboard_tab = DashboardTab()
        self.ingest_tab = DataIngestTab()
        self.network_tab = NetworkMonitorTab()
        self.incident_tab = IncidentResponseTab()
        self.pentest_tab = PentestingTab()
        self.ai_tab = AIAnalysisTab()
        self.chat_tab = ChatTab()
        self.notes_tab = NotesTab()
        self.logs_tab = LogsDatabaseTab()

        nav_map = [
            ("Dashboard", "Live hardware state, telemetry preview, and environment rollup.", self.dashboard_tab),
            ("Data Ingest", "Manage serial/TCP listeners and inspect incoming JSON streams.", self.ingest_tab),
            ("Network Monitor", "Track discovered devices and telemetry-driven traffic summary.", self.network_tab),
            ("Incident Response", "Review timeline, anomalies, and environment drift hooks.", self.incident_tab),
            ("Pentesting", "Authorized analysis workspace for PCAP review and evidence tags.", self.pentest_tab),
            ("AI Analysis", "Run local model analysis and capture threat classification output.", self.ai_tab),
            ("AI Chat", "Talk with the local NEXUS intelligence engine.", self.chat_tab),
            ("Notes Device", "Capture structured markdown notes linked to incidents and events.", self.notes_tab),
            ("Logs Database", "Query and filter persisted telemetry from SQLite storage.", self.logs_tab),
        ]

        self.nav_buttons: dict[str, QPushButton] = {}
        for label, section_subtitle, page in nav_map:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            side_layout.addWidget(button)
            self.nav_buttons[label] = button
            self.nav.add_page(page, button)
            self._section_meta.append((label, section_subtitle))

        side_layout.addStretch(1)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(14, 12, 14, 14)
        content_layout.setSpacing(10)

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar_layout = QVBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(14, 10, 14, 10)
        top_bar_layout.setSpacing(2)

        self.section_title = QLabel("Dashboard")
        self.section_title.setObjectName("SectionTitle")
        self.section_subtitle = QLabel("")
        self.section_subtitle.setObjectName("SectionSub")
        self.section_subtitle.setWordWrap(True)
        top_bar_layout.addWidget(self.section_title)
        top_bar_layout.addWidget(self.section_subtitle)

        content_layout.addWidget(top_bar)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content_container, 1)

        self.stack.currentChanged.connect(self._on_section_changed)
        self._on_section_changed(self.stack.currentIndex())

    def _on_section_changed(self, index: int) -> None:
        if 0 <= index < len(self._section_meta):
            title, subtitle = self._section_meta[index]
            self.section_title.setText(title)
            self.section_subtitle.setText(subtitle)

            widget = self.stack.widget(index)
            if widget:
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)

                self._fade_anim = QPropertyAnimation(effect, b"opacity")
                self._fade_anim.setDuration(250)
                self._fade_anim.setStartValue(0.0)
                self._fade_anim.setEndValue(1.0)
                self._fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                self._fade_anim.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
                self._fade_anim.start()

    def _init_status_bar(self) -> None:
        sb = self.statusBar()
        sb.setStyleSheet(
            "QStatusBar { background-color: #090f17; color: #6f8ca8; font-size: 11px; border-top: 1px solid #1f3448; }"
            "QStatusBar::item { border: none; }"
        )
        self._sb_serial = QLabel("Serial: [ ] Disconnected")
        self._sb_tcp = QLabel("TCP: [ ] Disconnected")
        self._sb_rows = QLabel("DB: 0 rows")
        self._sb_model = QLabel("Model: gemma3:4b")
        sb.addWidget(self._sb_serial)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._sb_tcp)
        sb.addWidget(QLabel("|"))
        sb.addWidget(self._sb_rows)
        sb.addPermanentWidget(self._sb_model)

    def update_status_bar(
        self,
        serial_connected: bool | None = None,
        serial_msg: str = "",
        tcp_connected: bool | None = None,
        tcp_msg: str = "",
        db_rows: int | None = None,
        model: str = "",
    ) -> None:
        """Update the persistent status bar labels."""
        if serial_connected is not None:
            icon = "[x]" if serial_connected else "[ ]"
            message = serial_msg or ("Connected" if serial_connected else "Disconnected")
            self._sb_serial.setText(f"Serial: {icon} {message}")
        if tcp_connected is not None:
            icon = "[x]" if tcp_connected else "[ ]"
            message = tcp_msg or ("Connected" if tcp_connected else "Disconnected")
            self._sb_tcp.setText(f"TCP: {icon} {message}")
        if db_rows is not None:
            self._sb_rows.setText(f"DB: {db_rows:,} rows")
        if model:
            self._sb_model.setText(f"Model: {model}")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if callable(self.on_close):
            self.on_close()
        super().closeEvent(event)
