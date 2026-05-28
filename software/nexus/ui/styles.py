DARK_THEME_STYLESHEET = """
QMainWindow, QWidget {
    color: #e2f0fd;
    font-family: "Segoe UI", "Inter", "Bahnschrift", sans-serif;
    font-size: 13px;
}

QWidget#AppRoot {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #050a11,
        stop: 0.5 #08111e,
        stop: 1 #0c1727
    );
}

QFrame#Sidebar {
    background: rgba(4, 8, 14, 0.95);
    border-right: 1px solid rgba(0, 240, 255, 0.12);
}

QFrame#BrandCard {
    background-color: rgba(14, 25, 41, 0.6);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 12px;
    padding: 10px;
}

QLabel#BrandTitle {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #ffffff;
    font-family: "Segoe UI Semibold", sans-serif;
}

QLabel#BrandSub {
    color: #7d9cb8;
    font-size: 11px;
}

QLabel#SidebarHint {
    color: #557596;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 1.5px;
    padding: 12px 2px 4px 2px;
}

QPushButton#NavButton {
    text-align: left;
    padding: 11px 16px;
    border: 1px solid transparent;
    border-left: 3px solid transparent;
    border-radius: 8px;
    background-color: transparent;
    color: #9dbacc;
    min-height: 20px;
}

QPushButton#NavButton:hover {
    background-color: rgba(0, 240, 255, 0.06);
    color: #ffffff;
    border-color: rgba(0, 240, 255, 0.15);
}

QPushButton#NavButton:checked {
    background-color: rgba(0, 240, 255, 0.12);
    border-color: rgba(0, 240, 255, 0.35);
    border-left: 3px solid #00f0ff;
    color: #ffffff;
    font-weight: 700;
}

QFrame#TopBar {
    background-color: rgba(10, 18, 30, 0.7);
    border: 1px solid rgba(0, 240, 255, 0.15);
    border-radius: 12px;
}

QLabel#SectionTitle {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#SectionSub {
    color: #8faec8;
    font-size: 12px;
}

QGroupBox {
    border: 1px solid rgba(0, 240, 255, 0.15);
    border-radius: 12px;
    margin-top: 18px;
    padding-top: 16px;
    background-color: rgba(7, 13, 23, 0.7);
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px 0 8px;
    color: #00f0ff;
    font-weight: 700;
}

QLineEdit, QPlainTextEdit, QTextEdit, QTableWidget, QListWidget, QSpinBox {
    background-color: rgba(4, 9, 16, 0.9);
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-radius: 8px;
    padding: 8px;
    color: #e2f0fd;
    selection-background-color: #00aeff;
    selection-color: #040910;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #00f0ff;
}

QPlainTextEdit, QTextEdit {
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}

QTableWidget {
    gridline-color: rgba(0, 240, 255, 0.08);
    alternate-background-color: rgba(6, 12, 22, 0.5);
}

QHeaderView::section {
    background-color: rgba(12, 23, 39, 0.8);
    color: #00f0ff;
    font-weight: 600;
    padding: 8px;
    border: 0;
    border-bottom: 1px solid rgba(0, 240, 255, 0.2);
}

QPushButton {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #005f87,
        stop: 1 #0087ba
    );
    border: 1px solid #00b8ff;
    border-radius: 8px;
    padding: 9px 16px;
    color: #ffffff;
    font-weight: 700;
}

QPushButton:hover {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #007bb0,
        stop: 1 #00a5de
    );
    border-color: #00f0ff;
}

QPushButton:pressed {
    background-color: #004d6e;
}

QPushButton:disabled {
    color: #4f6479;
    background-color: rgba(8, 16, 27, 0.6);
    border-color: rgba(0, 240, 255, 0.05);
}

QScrollBar:vertical {
    background: rgba(4, 9, 16, 0.5);
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(0, 240, 255, 0.25);
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #00f0ff;
}

QLabel[status="ok"] {
    color: #00ff88;
    font-weight: 700;
}

QLabel[status="warn"] {
    color: #ffc400;
    font-weight: 700;
}

QLabel[status="bad"] {
    color: #ff3b3f;
    font-weight: 700;
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
    border-radius: 16px;
    padding: 12px 18px;
    font-size: 13px;
    line-height: 1.6;
    margin-bottom: 8px;
}

QLabel#UserBubble {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #005f87,
        stop: 1 #0087ba
    );
    color: #ffffff;
    border: 1px solid #00b8ff;
    border-bottom-right-radius: 2px;
}

QLabel#AiBubble {
    background: rgba(14, 25, 41, 0.85);
    color: #e2f0fd;
    border: 1px solid rgba(0, 240, 255, 0.2);
    border-bottom-left-radius: 2px;
}

QLabel#ThinkingLabel {
    color: #799bbb;
    font-style: italic;
    font-size: 11px;
    padding-left: 10px;
}

/* Cancel / destructive button */
QPushButton#CancelBtn {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #6e1a1a,
        stop: 1 #962525
    );
    border: 1px solid #ff4d4d;
    color: #ffffff;
}

QPushButton#CancelBtn:hover {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 0,
        stop: 0 #8c2323,
        stop: 1 #b83232
    );
    border-color: #ff8080;
}

QPushButton#CancelBtn:disabled {
    background-color: rgba(22, 10, 10, 0.6);
    border-color: rgba(255, 77, 77, 0.05);
    color: #6a3e3e;
}
"""
