# QuickMeaning 🔍

**QuickMeaning** is a minimal, lightning-fast Windows desktop background utility that lets you instantly look up word meanings without leaving your active application.

---

## ⚡ Key Features

- **Global Shortcut**: Press `Ctrl + Shift + M` from any application (browser, PDF reader, text editor, IDE) to open the popup.
- **Fixed Command Palette**: Compact, fixed-size `420 × 300 px` dark slate window (`#181825`) with top-pinned search header.
- **Draggable Window**: Click and hold anywhere on the header or card frame to drag the popup to any screen position.
- **Clickable & Keyboard Dismiss**: Click the **"Esc to close"** button or press the physical `Esc` key to hide the window.
- **Clean Reopen Experience**: Every time the popup is reopened via `Ctrl + Shift + M`, previous results are cleared and the search field is reset with focus.
- **Smart Multilingual Lookup**:
  - Supports English words as well as foreign terms (*bonjour*, *schadenfreude*, *gracias*, *ephemeral*).
  - **Article & Headword Fallback**: Strips leading articles (`La fille` $\to$ `fille`, `L'eau` $\to$ `eau`, `Le garçon` $\to$ `garçon`) and phrasal spaces (`pop up` $\to$ `pop-up`).
  - **Relevancy Scoring**: Automatically prioritizes primary dictionary definitions (*Paris = Capital of France*) over obscure grammatical entries (*plural of pari*).
- **Dedicated Scroll Area**: Long definitions wrap naturally and scroll vertically without window distortion.
- **System Tray Utility**: Runs quietly in the Windows background with tray icon controls.
- **Connectivity Resilient**: Clear, friendly error messages for missing words, timeouts, and network failures.

---

## 🚀 Usage

### 1. Running from Source

```cmd
mean\Scripts\python main.py
```

### 2. Workflow

1. Press **`Ctrl + Shift + M`** anywhere in Windows.
2. Type any word or phrase (e.g. `ephemeral`, `Paris`, `La fille`, `pop up`).
3. Press **`Enter`** to view part of speech, language, and definition.
4. Press **`Esc`** or click **`Esc to close`** to dismiss the popup.

---

## 🛠️ Building Standalone Executable

To build the standalone executable `dist/QuickMeaning.exe`:

```cmd
mean\Scripts\python build.py
```

After building, double-click `dist/QuickMeaning.exe` to run QuickMeaning as a standalone Windows utility without requiring Python installed.

---

## 📁 Project Structure

```text
QuickMeaning/
├── main.py               # Background application entry point & system tray manager
├── ui.py                 # PySide6 fixed-size (420x300px) draggable command palette
├── dictionary.py         # Wiktionary API, article fallback, & definition relevancy scorer
├── hotkey.py             # Global shortcut listener (pynput + thread-safe Qt Signals)
├── config.py             # Application settings, API endpoints, colors, & dimensions
├── build.py              # PyInstaller executable build script
├── rthook_six_patch.py   # PyInstaller runtime hook for Python 3.12 compatibility
├── QuickMeaning.spec     # PyInstaller configuration specification
├── requirements.txt      # Python dependencies
├── .gitignore            # Git exclusion rules
├── assets/
│   ├── icon.png          # App PNG icon
│   └── icon.ico          # Executable & Tray ICO icon
└── README.md             # Project documentation
```
