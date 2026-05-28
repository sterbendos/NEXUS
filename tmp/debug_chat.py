import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from nexus.ui.tabs.chat_tab import ChatTab
from nexus.ui.styles import DARK_THEME_STYLESHEET

def test_ui():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_STYLESHEET)
    
    win = QMainWindow()
    tab = ChatTab()
    win.setCentralWidget(tab)
    win.show()
    
    print("Adding test message...")
    try:
        tab.add_message("Hello Test", "user")
        print("Success user")
        tab.add_message("I am AI response", "ai")
        print("Success ai")
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)
        
    print("Closing test in 2 seconds...")
    # sys.exit(app.exec()) # Keep open to check visually? 
    # For now just exit success if no crash
    return 0

if __name__ == "__main__":
    test_ui()
