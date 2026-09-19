"""
Global hotkey listener module for QuickMeaning using pynput.
Emits a PySide6 Signal when Ctrl + Shift + M is pressed.
"""

from PySide6.QtCore import QObject, Signal
from pynput import keyboard
from config import HOTKEY_STR


class HotkeyListener(QObject):
    # Thread-safe Signal emitted when hotkey is triggered
    triggered = Signal()

    def __init__(self, hotkey_str: str = HOTKEY_STR):
        super().__init__()
        self.hotkey_str = hotkey_str
        self._listener = None

    def start(self):
        """Start listening for the global hotkey in a background thread."""
        try:
            self._listener = keyboard.GlobalHotKeys({
                self.hotkey_str: self._on_triggered
            })
            self._listener.start()
        except Exception as e:
            print(f"Error starting global hotkey listener: {e}")

    def _on_triggered(self):
        """Callback invoked by pynput thread when hotkey is pressed."""
        self.triggered.emit()

    def stop(self):
        """Stop listening for global hotkeys."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
