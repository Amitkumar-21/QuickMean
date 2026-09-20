# QuickMean ⚡

**QuickMean** is a minimal, lightning-fast Windows desktop background utility that lets you instantly look up word meanings and pronunciations from anywhere using a global hotkey.

---

## ✨ Features

- **Global Hotkey (`Ctrl + Shift + M`)**: Trigger a sleek search palette instantly from any application (browser, PDF, IDE, reader).
- **Dual Dictionary Engine**:
  - **Free Dictionary API**: Primary source for English single-word lookups and IPA phonetics.
  - **Wiktionary API**: Multilingual support (*bonjour*, *fille*, *schadenfreude*) with automatic article stripping (`La fille` → `fille`).
- **Smart Relevancy Scoring**: Automatically prioritizes primary English and living language meanings while filtering out obscure Translingual/ISO symbol fallbacks.
- **Modern Dark UI**: Frameless, fixed-size (`420 × 300px`) command palette with dark slate styling, mouse dragging, vertical scroll area, and `Esc` key dismissal.
- **Background System Tray**: Runs quietly in the Windows system tray with low memory footprint.

---

## 🚀 Quick Start

### 1. Run from Source

```cmd
python main.py
```

### 2. Workflow

1. Press **`Ctrl + Shift + M`** anywhere in Windows.
2. Type any word or phrase (e.g., `ask`, `serendipity`, `bonjour`, `La fille`).
3. Press **`Enter`** to view part of speech, pronunciation, language, and definition.
4. Press **`Esc`** or click **Esc to close** to dismiss the palette.

---

## 🛠️ Building Standalone Executable

To package QuickMean into a single standalone `.exe` using PyInstaller:

```cmd
python build.py
```

The compiled standalone executable will be created at `dist/QuickMeaning.exe`.

---

## 📁 Project Structure

```text
QuickMean/
├── main.py               # Background app entry point & system tray manager
├── ui.py                 # PySide6 fixed-size draggable command palette
├── dictionary.py         # Free Dictionary API + Wiktionary scoring engine
├── hotkey.py             # Global shortcut listener (pynput + Qt Signals)
├── config.py             # Application settings, palette colors, & layout dimensions
├── build.py              # PyInstaller executable build script
├── rthook_six_patch.py   # PyInstaller runtime hook for Python 3.12 compatibility
├── QuickMeaning.spec     # PyInstaller configuration specification
├── requirements.txt      # Python dependencies (PySide6, pynput)
├── assets/               # Application & system tray icons
└── README.md             # Project documentation
```
