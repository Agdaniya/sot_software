"""
Font loader — call load_fonts() once at app startup (before any QWidget is created).
Drop Inter TTF files into  sot_software/assets/fonts/  and they will be used.
Falls back to Segoe UI → system sans-serif if files are not present.
"""
import os, sys
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication


def _assets_dir() -> str:
    if getattr(sys, "frozen", False):
        # --onefile: PyInstaller extracts datas into sys._MEIPASS, not next to the exe
        return os.path.join(sys._MEIPASS, "assets", "fonts")
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
    )


def load_fonts() -> str:
    """
    Register bundled TTF files with Qt and return the family name to use.
    Priority: Inter → Manrope → Segoe UI
    """
    font_dir = _assets_dir()
    loaded   = []

    if os.path.isdir(font_dir):
        for fname in sorted(os.listdir(font_dir)):
            if fname.lower().endswith((".ttf", ".otf")):
                path = os.path.join(font_dir, fname)
                fid  = QFontDatabase.addApplicationFont(path)
                if fid >= 0:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    loaded.extend(families)

    # Pick best available family
    available = QFontDatabase.families()
    for preferred in ("Inter", "Manrope", "Segoe UI", "SF Pro Display", "Helvetica Neue"):
        if any(preferred.lower() in f.lower() for f in (loaded + list(available))):
            return preferred

    return "Arial"


def apply_font(app: QApplication, family: str = None):
    """Call once after QApplication is created."""
    if family is None:
        family = load_fonts()
    font = QFont(family, 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)
    return family
