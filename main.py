"""
Main application entry point for QuickMeaning.
Runs in the background, listens for Ctrl + Shift + M, and manages system tray icon.
"""

import sys
import os

# Fix incompatibility between Shiboken6 (PySide6) and six (pynput) under Python 3.12
try:
    import six
    if hasattr(six, "_SixMetaPathImporter") and not hasattr(six._SixMetaPathImporter, "_path"):
        six._SixMetaPathImporter._path = None
except Exception:
    pass

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

from config import APP_NAME, HOTKEY_DISPLAY
from ui import QuickMeaningWindow
from hotkey import HotkeyListener


def get_icon_path() -> str:
    """Resolve asset icon path for dev environment and PyInstaller standalone build."""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    ico_path = os.path.join(base_dir, 'assets', 'icon.ico')
    png_path = os.path.join(base_dir, 'assets', 'icon.png')
    
    if os.path.exists(ico_path):
        return ico_path
    elif os.path.exists(png_path):
        return png_path
    return ""


def main():
    app = QApplication(sys.argv)
    
    # Crucial: Keep app running in background when popup is hidden
    app.setQuitOnLastWindowClosed(False)
    
    icon_path = get_icon_path()
    if icon_path:
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        app_icon = QIcon()

    # Instantiate UI window
    window = QuickMeaningWindow()

    # Configure System Tray Icon
    tray_icon = QSystemTrayIcon(app_icon, app)
    tray_icon.setToolTip(f"{APP_NAME} ({HOTKEY_DISPLAY})")

    tray_menu = QMenu()
    
    show_action = QAction(f"Lookup Word ({HOTKEY_DISPLAY})", app)
    show_action.triggered.connect(window.show_and_focus)
    tray_menu.addAction(show_action)

    tray_menu.addSeparator()

    quit_action = QAction("Quit QuickMeaning", app)
    quit_action.triggered.connect(app.quit)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(
        lambda reason: window.show_and_focus()
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick)
        else None
    )
    tray_icon.show()

    # Initialize Global Hotkey Listener (Ctrl + Shift + M)
    hotkey_listener = HotkeyListener()
    hotkey_listener.triggered.connect(window.show_and_focus)
    hotkey_listener.start()

    # Cleanup listener on exit
    app.aboutToQuit.connect(hotkey_listener.stop)

    print(f"QuickMeaning running in background. Press {HOTKEY_DISPLAY} to activate.")
    
    # Execute Qt Event Loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
