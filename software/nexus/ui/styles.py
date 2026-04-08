DARK_THEME_STYLESHEET = """
QMainWindow, QWidget {
    color: #d7e4f3;
    font-family: "Bahnschrift", "Trebuchet MS", sans-serif;
    font-size: 13px;
}

QWidget#AppRoot {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #09121d,
        stop: 0.45 #0c1623,
        stop: 1 #111d2c
    );
}

QFrame#Sidebar {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #0c1826,
        stop: 1 #0b1420
    );
    border-right: 1px solid #1f3448;
}

QFrame#BrandCard {
    background-color: #122338;
    border: 1px solid #2d4962;
    border-radius: 12px;
    padding: 8px;
}

QLabel#BrandTitle {
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #f3f8ff;
}

QLabel#BrandSub {
    color: #9ab4cd;
    font-size: 11px;
}

QLabel#SidebarHint {
    color: #6f8ca8;
    font-size: 11px;
    padding: 4px 2px;
}

QPushButton#NavButton {
    text-align: left;
    padding: 10px 14px;
    border: 1px solid transparent;
    border-left: 4px solid transparent;
    border-radius: 10px;
    background-color: transparent;
    color: #bfd0e2;
    min-height: 20px;
}

QPushButton#NavButton:hover {
    background-color: #16283b;
    border-color: #2a445e;
}

QPushButton#NavButton:checked {
    background-color: #1b3450;
    border-color: #3c5f7f;
    border-left: 4px solid #79d5ff;
    color: #f3fbff;
    font-weight: 600;
}

QFrame#TopBar {
    background-color: rgba(16, 34, 52, 0.9);
    border: 1px solid #2a435c;
    border-radius: 12px;
}

QLabel#SectionTitle {
    font-size: 18px;
    font-weight: 700;
    color: #f3f8ff;
}

QLabel#SectionSub {
    color: #9ab4cd;
    font-size: 12px;
}

QGroupBox {
    border: 1px solid #2b4259;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 12px;
    background-color: rgba(15, 29, 44, 0.92);
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px 0 6px;
    color: #a5c1dc;
}

QLineEdit, QPlainTextEdit, QTextEdit, QTableWidget, QListWidget, QSpinBox {
    background-color: #101d2b;
    border: 1px solid #304a63;
    border-radius: 8px;
    padding: 7px;
    selection-background-color: #2b7aaa;
    selection-color: #f1f9ff;
}

QPlainTextEdit, QTextEdit {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}

QTableWidget {
    gridline-color: #28445c;
    alternate-background-color: #122436;
}

QHeaderView::section {
    background-color: #152738;
    color: #bad0e5;
    padding: 7px;
    border: 0;
    border-bottom: 1px solid #2f4d67;
}

QPushButton {
    background-color: #1a4b6b;
    border: 1px solid #377295;
    border-radius: 8px;
    padding: 8px 13px;
    color: #e8f5ff;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #246086;
}

QPushButton:pressed {
    background-color: #184663;
}

QPushButton:disabled {
    color: #70869c;
    background-color: #142739;
    border-color: #274057;
}

QScrollBar:vertical {
    background: #0f1e2d;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2f5878;
    border-radius: 5px;
    min-height: 24px;
}

QLabel[status="ok"] {
    color: #88e7b1;
    font-weight: 600;
}

QLabel[status="warn"] {
    color: #ffd38c;
    font-weight: 600;
}

QLabel[status="bad"] {
    color: #ff9fa1;
    font-weight: 600;
}

/* AI Chat Styling */
QScrollArea#ChatScroll {
    background-color: transparent;
    border: none;
}

QWidget#ChatContent {
    background-color: transparent;
}

QLabel#ChatBubble {
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
    line-height: 1.4;
    margin-bottom: 4px;
}

QLabel#UserBubble {
    background-color: #1a4b6b;
    color: #e8f5ff;
    border: 1px solid #377295;
    border-bottom-right-radius: 2px;
}

QLabel#AiBubble {
    background-color: rgba(30, 48, 68, 0.85);
    color: #d7e4f3;
    border: 1px solid #2d4962;
    border-bottom-left-radius: 2px;
}

QLabel#ThinkingLabel {
    color: #6f8ca8;
    font-style: italic;
    font-size: 11px;
    padding-left: 10px;
}
"""
