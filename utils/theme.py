"""
SOT Design System
-----------------
Single source of truth for every colour, radius, and shared stylesheet.
Import from here instead of copy-pasting hex strings in every file.
"""

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#F4F5F7"        # page background (light grey)
SURFACE     = "#FFFFFF"        # card / panel
BORDER      = "#E8EAED"        # subtle dividers
BORDER_MED  = "#D1D5DB"        # medium emphasis border

TEXT        = "#111827"        # primary text
TEXT_SEC    = "#6B7280"        # secondary / muted text
TEXT_HINT   = "#9CA3AF"        # placeholder / hint

ACCENT      = "#2563EB"        # primary blue (buttons, links, active states)
ACCENT_DARK = "#1D4ED8"        # hover
ACCENT_BG   = "#EFF6FF"        # very light blue tint

SUCCESS     = "#16A34A"
SUCCESS_BG  = "#F0FDF4"
WARNING     = "#D97706"
WARNING_BG  = "#FFFBEB"
DANGER      = "#DC2626"
DANGER_BG   = "#FEF2F2"

RADIUS      = "10px"
RADIUS_SM   = "6px"
RADIUS_LG   = "14px"

# ── Role badge colours ────────────────────────────────────────────────────────
ROLE_COLORS = {
    "super_admin": ("#7C3AED", "#F5F3FF"),   # purple text, purple bg
    "admin":       ("#2563EB", "#EFF6FF"),   # blue text, blue bg
    "employee":    ("#374151", "#F3F4F6"),   # grey text, grey bg
}

# ── Status colours ────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "not_started":    ("#6B7280", "#F3F4F6"),
    "in_progress":    ("#D97706", "#FFFBEB"),
    "submitted":      ("#7C3AED", "#F5F3FF"),
    "admin_approved": ("#16A34A", "#F0FDF4"),
    "admin_rejected": ("#DC2626", "#FEF2F2"),
    "client_approved":("#0891B2", "#ECFEFF"),
    "completed":      ("#2563EB", "#EFF6FF"),
}

# ── Shared QSS snippets ───────────────────────────────────────────────────────
def app_base():
    return f"""
        QWidget {{
            background: {BG};
            font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            font-size: 13px;
            color: {TEXT};
        }}
    """

def card():
    return f"""
        QFrame {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: {RADIUS};
        }}
    """

def card_no_border():
    return f"""
        QFrame {{
            background: {SURFACE};
            border: none;
            border-radius: {RADIUS};
        }}
    """

def input_field():
    return f"""
        QLineEdit {{
            padding: 10px 14px;
            border: 1.5px solid {BORDER};
            border-radius: {RADIUS_SM};
            font-size: 13px;
            background: {SURFACE};
            color: {TEXT};
        }}
        QLineEdit:focus {{
            border: 1.5px solid {ACCENT};
            background: {SURFACE};
        }}
        QLineEdit::placeholder {{
            color: {TEXT_HINT};
        }}
    """

def input_field_flat():
    """Input with grey background (for forms on white cards)"""
    return f"""
        QLineEdit {{
            padding: 10px 14px;
            border: 1.5px solid {BORDER};
            border-radius: {RADIUS_SM};
            font-size: 13px;
            background: {BG};
            color: {TEXT};
        }}
        QLineEdit:focus {{
            border: 1.5px solid {ACCENT};
            background: {SURFACE};
        }}
        QLineEdit::placeholder {{
            color: {TEXT_HINT};
        }}
    """

def btn_primary():
    return f"""
        QPushButton {{
            background: {ACCENT};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {ACCENT_DARK};
        }}
        QPushButton:pressed {{
            background: {ACCENT_DARK};
        }}
        QPushButton:disabled {{
            background: {BORDER_MED};
            color: {TEXT_HINT};
        }}
    """

def btn_secondary():
    return f"""
        QPushButton {{
            background: {SURFACE};
            color: {TEXT};
            border: 1.5px solid {BORDER};
            border-radius: {RADIUS_SM};
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            border-color: {BORDER_MED};
            background: {BG};
        }}
        QPushButton:disabled {{
            color: {TEXT_HINT};
        }}
    """

def btn_danger():
    return f"""
        QPushButton {{
            background: {SURFACE};
            color: {DANGER};
            border: 1.5px solid {DANGER};
            border-radius: {RADIUS_SM};
            padding: 10px 20px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {DANGER_BG};
        }}
        QPushButton:disabled {{
            color: {TEXT_HINT};
            border-color: {BORDER};
        }}
    """

def list_widget():
    return f"""
        QListWidget {{
            border: none;
            background: transparent;
            outline: none;
        }}
        QListWidget::item {{
            padding: 12px 14px;
            border: 1.5px solid {BORDER};
            border-radius: {RADIUS_SM};
            margin-bottom: 6px;
            background: {SURFACE};
            color: {TEXT};
        }}
        QListWidget::item:hover {{
            border-color: {BORDER_MED};
            background: {BG};
        }}
        QListWidget::item:selected {{
            border: 1.5px solid {ACCENT};
            background: {ACCENT_BG};
            color: {TEXT};
        }}
    """

def status_badge_style(status: str) -> str:
    fg, bg = STATUS_COLORS.get(status, (TEXT_SEC, BG))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
        f"padding: 3px 10px; font-size: 11px; font-weight: 700; }}"
    )

def role_badge_style(role: str) -> str:
    fg, bg = ROLE_COLORS.get(role, (TEXT_SEC, BG))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
        f"padding: 3px 10px; font-size: 11px; font-weight: 700; }}"
    )
