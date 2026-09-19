"""
Build script for packaging QuickMeaning into a standalone executable using PyInstaller.
Creates dist/QuickMeaning.exe.
"""

import os
import sys
import subprocess

def build():
    print("Building QuickMeaning standalone Windows executable...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, 'assets')
    icon_path = os.path.join(assets_dir, 'icon.ico')
    rthook_path = os.path.join(base_dir, 'rthook_six_patch.py')

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=QuickMeaning",
        "--clean"
    ]

    if os.path.exists(rthook_path):
        cmd.append(f"--runtime-hook={rthook_path}")

    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    # Add assets directory data
    cmd.append(f"--add-data={assets_dir};assets")

    # Target entry point
    cmd.append(os.path.join(base_dir, "main.py"))

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        exe_path = os.path.join(base_dir, "dist", "QuickMeaning.exe")
        print(f"\nBuild successful! Executable created at:\n{exe_path}")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")

if __name__ == "__main__":
    build()
