"""
Configuration constants for QuickMeaning.
"""

APP_NAME = "QuickMeaning"
APP_VERSION = "1.0.0"

# Global Shortcut (pynput format)
HOTKEY_STR = "<ctrl>+<shift>+m"
HOTKEY_DISPLAY = "Ctrl + Shift + M"

# Dictionary APIs
WIKTIONARY_API_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/"
FREE_DICTIONARY_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

# Network Configuration
REQUEST_TIMEOUT = 5.0  # seconds
USER_AGENT = "QuickMeaning/1.0 (Windows Desktop Utility)"

# UI Layout Dimensions (Fixed Window Size)
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 300

# Dark Theme Palette
COLOR_BG = "#181825"         # Dark slate surface
COLOR_CARD = "#1e1e2e"       # Card / Container background
COLOR_BORDER = "#313244"     # Subtle border color
COLOR_TEXT_PRIMARY = "#cdd6f4" # High contrast text
COLOR_TEXT_MUTED = "#a6adc8"   # Secondary text / labels
COLOR_ACCENT = "#89b4fa"     # Blue accent (brand color)
COLOR_PRONUNCIATION = "#f9e2af" # Soft gold for phonetics
COLOR_ERROR = "#f38ba8"      # Soft red for error messages
