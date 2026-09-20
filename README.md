# QuickMeaning 🔍

**QuickMeaning** is a minimal Windows desktop background utility that lets you look up word meanings and pronunciations instantly using a global keyboard shortcut.

---

## 📸 Screenshot

![QuickMeaning UI](assets/screenshot.png)

---

## ✨ Features

- **Global Shortcut**: Press `Ctrl + Shift + M` anywhere in Windows to trigger the search popup.
- **Start with Windows**: Automatically start QuickMeaning silently in the system tray after Windows login without administrator privileges.
- **System Tray Controls**: Easily enable or disable automatic startup directly from the system-tray context menu.
- **Silent Background Launch**: Starts in the system tray without opening the search popup window on startup.
- **Clean Input State**: Search input field clears automatically every time the window is reopened.
- **Keyboard & Mouse Control**:
  - Press `Enter` to submit search.
  - Press `Esc` or click the **Esc to close** badge to dismiss the window.
- **Fixed & Draggable Palette**: A compact, fixed-size command palette (`420 × 300 px`) that can be dragged by clicking and holding the header or frame.
- **Scrollable Results Area**: Result display area wraps long definitions and scrolls vertically when needed.
- **Multilingual Support**: Lookup support for English as well as foreign-language words (*bonjour*, *fille*, *schadenfreude*).
- **Article Normalization**: Automatically strips leading articles (e.g., `La fille` → `fille`) and handles phrasal queries.
- **Smart Relevancy Scoring**: Automatically prioritizes primary dictionary definitions while filtering out obscure Translingual or ISO language code entries.

---

## ⚙️ How It Works

### Automatic Startup Workflow

```text
Windows Login
     ↓
QuickMeaning starts
     ↓
System Tray
     ↓
Ctrl + Shift + M
     ↓
Search Popup
     ↓
Dictionary Result
```

### Manual Launch Workflow

```text
Launch QuickMeaning (python main.py or executable)
     ↓
System Tray
     ↓
Ctrl + Shift + M
     ↓
Search Popup
     ↓
Dictionary Result
```

1. QuickMeaning runs quietly in the background with a system tray icon (launched manually or automatically after Windows login).
2. Pressing `Ctrl + Shift + M` triggers a thread-safe signal that centers and focuses the frameless command palette popup.
3. Single-word queries first check the **Free Dictionary API** for English definitions and IPA phonetics.
4. If unavailable or when searching foreign words, the query falls back to the **Wiktionary REST API**, applying article normalization and relevancy scoring to deliver the best definition.
5. *Note: Dictionary lookups require an active internet connection to query online APIs.*

---

## 🚀 Getting Started

### Prerequisites

- Windows 10 or 11
- Python 3.10+ installed and added to PATH
- Active internet connection (required for dictionary lookups)

### Installation

Clone the repository and set up a Python virtual environment:

```cmd
git clone https://github.com/Amitkumar-21/QuickMean.git
cd QuickMean
python -m venv mean
mean\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 🎯 Usage

### Basic Usage

1. Start QuickMeaning manually by running `python main.py` or double-clicking `dist/QuickMeaning.exe`, or let it launch automatically after Windows login.
2. Once QuickMeaning is running in the background, the global shortcut **`Ctrl + Shift + M`** is available from any active application (browser, PDF reader, IDE, text editor).
3. Type any word or phrase (e.g., `ask`, `serendipity`, `bonjour`, `La fille`).
4. Press **`Enter`** to view part of speech, pronunciation, language, and definition.
5. Press **`Esc`** or click **Esc to close** to hide the popup.

### System Tray & Start with Windows

- **Start with Windows**:
  1. Right-click the QuickMeaning system-tray icon.
  2. Enable **Start with Windows** to automatically launch QuickMeaning after Windows login.
  3. Disable it anytime to prevent automatic startup.
- **Session vs. Startup Preference**:
  - Selecting **Exit** from the tray menu closes QuickMeaning for the current session only; it does **not** disable your startup preference.
- **Global Hotkey Availability**:
  - The global shortcut **`Ctrl + Shift + M`** is available whenever QuickMeaning is running in the background.

---

## 🛠️ Tech Stack

- **Python**: Core application language
- **PySide6**: Qt framework for desktop UI & system tray
- **pynput**: Global hotkey listener
- **httpx / urllib**: Network requests for dictionary APIs
- **Free Dictionary API**: Primary English definitions & IPA phonetics
- **Wiktionary REST API**: Multilingual lookup fallback engine
- **PyInstaller**: Standalone Windows executable packaging

---

## 📦 Build Instructions

To compile QuickMeaning into a standalone single-file Windows executable (`dist/QuickMeaning.exe`):

```cmd
python build.py
```

The script cleans previous build caches and outputs the compiled executable at `dist/QuickMeaning.exe`.

---

## 📁 Project Structure

```text
QuickMeaning/
├── main.py               # Application entry point & system tray manager
├── ui.py                 # PySide6 fixed-size, draggable command palette UI
├── dictionary.py         # Free Dictionary API & Wiktionary scoring logic
├── hotkey.py             # Global hotkey listener (pynput + Qt Signals)
├── autostart.py          # Windows startup shortcut management (no admin required)
├── config.py             # Configuration constants, colors, & dimensions
├── build.py              # PyInstaller automated build script
├── rthook_six_patch.py   # PyInstaller runtime hook for Python 3.12 compatibility
├── QuickMeaning.spec     # PyInstaller configuration specification
├── requirements.txt      # Project dependencies
├── assets/               # Application icons & UI screenshot (icon.png, icon.ico, screenshot.png)
└── README.md             # Project documentation
```

---

## 🔮 Future Ideas

- **Selected-Text Lookup**: Automatically populate search with currently highlighted text.
- **Customizable Hotkey**: Allow users to configure shortcut key combinations.
- **Context-Aware Explanations**: Provide AI/LLM-powered contextual definitions.
- **Word History**: Track recently searched words and definitions.
- **Offline Dictionary Support**: Local SQLite/Stardict dictionary fallback.

---

## 📄 License

This project is licensed under the MIT License.

