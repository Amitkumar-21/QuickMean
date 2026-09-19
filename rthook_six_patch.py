"""
PyInstaller runtime hook for QuickMeaning.
Fixes Python 3.12.0 importlib compatibility with six._SixMetaPathImporter
before PySide6 / Shiboken runtime hooks execute.
"""

try:
    import six
    if hasattr(six, "_SixMetaPathImporter") and not hasattr(six._SixMetaPathImporter, "_path"):
        six._SixMetaPathImporter._path = None
except Exception:
    pass
