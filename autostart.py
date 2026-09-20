r"""
Windows Startup management for QuickMeaning.
Uses standard Windows per-user Startup folder shortcuts (%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup)
to allow starting with Windows without requiring Administrator privileges.
"""

import sys
import os
import subprocess
import winreg

SHORTCUT_NAME = "QuickMeaning.lnk"
LEGACY_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
LEGACY_APP_KEY = "QuickMeaning"


def get_startup_folder_path() -> str:
    """Get the path to the current user's Windows Startup folder."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
    return os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")


def get_shortcut_path() -> str:
    """Get the absolute path to the QuickMeaning.lnk shortcut file in the Startup folder."""
    return os.path.join(get_startup_folder_path(), SHORTCUT_NAME)


def get_app_exe_path() -> str:
    """
    Get the absolute path to the QuickMeaning executable.
    When frozen (PyInstaller packaged EXE), returns sys.executable.
    In dev mode, returns the built executable in dist/ if present, or sys.executable as fallback.
    """
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dist_exe = os.path.join(base_dir, "dist", "QuickMeaning.exe")
        if os.path.exists(dist_exe):
            return os.path.abspath(dist_exe)
        return os.path.abspath(sys.executable)


def _clean_legacy_registry():
    """Remove any legacy HKCU Registry autostart entry if present."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, LEGACY_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, LEGACY_APP_KEY)
    except Exception:
        pass


def is_autostart_enabled() -> bool:
    """
    Check whether QuickMeaning startup shortcut exists in the user's Startup folder.
    """
    return os.path.exists(get_shortcut_path())


def create_shortcut(shortcut_path: str, target_path: str) -> bool:
    """
    Create a Windows shortcut (.lnk) pointing to target_path at shortcut_path.
    """
    try:
        startup_dir = os.path.dirname(shortcut_path)
        if not os.path.exists(startup_dir):
            os.makedirs(startup_dir, exist_ok=True)

        working_dir = os.path.dirname(target_path)
        safe_shortcut = shortcut_path.replace("'", "''")
        safe_target = target_path.replace("'", "''")
        safe_dir = working_dir.replace("'", "''")

        ps_cmd = (
            f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{safe_shortcut}'); "
            f"$s.TargetPath = '{safe_target}'; "
            f"$s.WorkingDirectory = '{safe_dir}'; "
            f"$s.Save()"
        )
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        res = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            creationflags=flags
        )
        return res.returncode == 0 and os.path.exists(shortcut_path)
    except Exception as e:
        print(f"Error creating startup shortcut: {e}")
        return False


def remove_shortcut(shortcut_path: str) -> bool:
    """
    Remove the QuickMeaning shortcut from the user's Startup folder.
    """
    try:
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
        return True
    except Exception as e:
        print(f"Error removing startup shortcut: {e}")
        return False


def set_autostart(enable: bool) -> bool:
    """
    Enable or disable QuickMeaning in Windows Startup folder.
    Returns True on success, False on failure.
    """
    shortcut_path = get_shortcut_path()
    _clean_legacy_registry()
    if enable:
        exe_path = get_app_exe_path()
        return create_shortcut(shortcut_path, exe_path)
    else:
        return remove_shortcut(shortcut_path)


def get_shortcut_target(shortcut_path: str) -> str:
    """
    Read the TargetPath of an existing shortcut.
    """
    if not os.path.exists(shortcut_path):
        return ""
    try:
        safe_shortcut = shortcut_path.replace("'", "''")
        ps_cmd = f"(New-Object -ComObject WScript.Shell).CreateShortcut('{safe_shortcut}').TargetPath"
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        res = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            creationflags=flags
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception as e:
        print(f"Error reading shortcut target: {e}")
    return ""


def sync_autostart_path():
    """
    If autostart is enabled (shortcut exists), verify that the shortcut points to the current executable.
    Updates the shortcut if the executable path has changed.
    """
    shortcut_path = get_shortcut_path()
    _clean_legacy_registry()
    if os.path.exists(shortcut_path):
        current_exe = get_app_exe_path()
        existing_target = get_shortcut_target(shortcut_path)
        if not existing_target or os.path.abspath(existing_target).lower() != os.path.abspath(current_exe).lower():
            set_autostart(True)
