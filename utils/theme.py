"""
SOT Design System — aligned with SOT React design
Single source of truth for every colour, radius, and shared stylesheet.
"""

# ── Palette (from React globals.css :root) ────────────────────────────────────
BG          = "#F7F8FA"        # --secondary / page background
SURFACE     = "#FFFFFF"        # --background / card
BORDER      = "rgba(0,0,0,0.10)"  # --border
BORDER_SOLID = "#E5E7EB"       # solid equivalent for QSS

TEXT        = "#030213"        # --primary / --foreground
TEXT_SEC    = "#717182"        # --muted-foreground
TEXT_HINT   = "#9CA3AF"        # placeholder

ACCENT      = "#030213"        # --primary (dark)
ACCENT_DARK = "#1a1a2e"        # hover on primary
ACCENT_BG   = "#ECECF0"        # --muted (tint for active states)

SUCCESS     = "#16A34A"        # teal-600 equivalent
SUCCESS_BG  = "#F0FDF4"
WARNING     = "#D97706"        # amber-700
WARNING_BG  = "#FFFBEB"
DANGER      = "#D4183D"        # --destructive
DANGER_BG   = "#FFF1F2"
DANGER_DARK = "#B0132F"

# Teal for client-approved / approve actions
TEAL        = "#0F766E"
TEAL_BG     = "#F0FDFA"

# Indigo for submitted
INDIGO      = "#4338CA"
INDIGO_BG   = "#EEF2FF"

RADIUS      = "10px"
RADIUS_SM   = "6px"
RADIUS_LG   = "12px"
RADIUS_XL   = "14px"

FONT        = "'Segoe UI', 'Inter', 'Arial', sans-serif"

# ── Role badge colours ────────────────────────────────────────────────────────
ROLE_COLORS = {
    "super_admin": ("#1D4ED8", "#DBEAFE"),   # blue-700, blue-100
    "admin":       ("#6D28D9", "#EDE9FE"),   # violet-700, violet-100
    "employee":    ("#374151", "#F3F4F6"),   # gray text, gray bg
}

# ── Status colours ────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "not_started":    ("#6B7280", "#F3F4F6"),   # gray
    "in_progress":    ("#B45309", "#FEF3C7"),   # amber
    "submitted":      ("#4338CA", "#EEF2FF"),   # indigo
    "admin_approved": ("#0F766E", "#F0FDFA"),   # teal
    "admin_rejected": ("#D4183D", "#FFF1F2"),   # red
    "client_approved":("#0F766E", "#F0FDFA"),   # teal
    "rejected":       ("#D4183D", "#FFF1F2"),   # red
    "completed":      ("#0F766E", "#F0FDFA"),   # teal
}

STATUS_DOT = {
    "not_started":    "#9CA3AF",
    "in_progress":    "#D97706",
    "submitted":      "#4338CA",
    "admin_approved": "#0F766E",
    "admin_rejected": "#D4183D",
    "client_approved":"#0F766E",
    "rejected":       "#D4183D",
    "completed":      "#0F766E",
}

STATUS_LABELS = {
    "not_started":    "Not Started",
    "in_progress":    "In Progress",
    "submitted":      "Submitted",
    "admin_approved": "Admin Approved",
    "admin_rejected": "Rejected",
    "client_approved":"Client Approved",
    "rejected":       "Rejected",
    "completed":      "Completed",
}

# ── Global QSS base ───────────────────────────────────────────────────────────
def app_base():
    return f"""
        QWidget {{
            background: {BG};
            font-family: {FONT};
            font-size: 13px;
            color: {TEXT};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {BORDER_SOLID};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {BORDER_SOLID};
            border-radius: 3px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """

# ── Card / panel ──────────────────────────────────────────────────────────────
def card():
    return f"""
        QFrame {{
            background: {SURFACE};
            border: 1px solid {BORDER_SOLID};
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

# ── Input fields ──────────────────────────────────────────────────────────────
def input_field():
    return f"""
        QLineEdit, QTextEdit {{
            padding: 8px 12px;
            border: 1px solid {BORDER_SOLID};
            border-radius: {RADIUS_SM};
            font-size: 13px;
            background: {SURFACE};
            color: {TEXT};
            selection-background-color: {ACCENT_BG};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1.5px solid {ACCENT};
            outline: none;
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {TEXT_HINT};
        }}
    """

def input_field_flat():
    """Input with page-background fill (for use on white cards)."""
    return f"""
        QLineEdit, QTextEdit {{
            padding: 8px 12px;
            border: 1px solid {BORDER_SOLID};
            border-radius: {RADIUS_SM};
            font-size: 13px;
            background: {BG};
            color: {TEXT};
            selection-background-color: {ACCENT_BG};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1.5px solid {ACCENT};
            background: {SURFACE};
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {TEXT_HINT};
        }}
    """

# ── Buttons ───────────────────────────────────────────────────────────────────
def btn_primary():
    return f"""
        QPushButton {{
            background: {ACCENT};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {ACCENT_DARK}; }}
        QPushButton:pressed {{ background: {ACCENT_DARK}; }}
        QPushButton:disabled {{
            background: {BORDER_SOLID};
            color: {TEXT_HINT};
        }}
    """

def btn_secondary():
    return f"""
        QPushButton {{
            background: {SURFACE};
            color: {TEXT};
            border: 1px solid {BORDER_SOLID};
            border-radius: {RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {BG};
            border-color: #C0C0C8;
        }}
        QPushButton:disabled {{ color: {TEXT_HINT}; }}
    """

def btn_danger():
    return f"""
        QPushButton {{
            background: {SURFACE};
            color: {DANGER};
            border: 1px solid #FECDD3;
            border-radius: {RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {DANGER_BG}; }}
        QPushButton:disabled {{ color: {TEXT_HINT}; border-color: {BORDER_SOLID}; }}
    """

def btn_danger_filled():
    return f"""
        QPushButton {{
            background: {DANGER};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {DANGER_DARK}; }}
        QPushButton:disabled {{ background: {BORDER_SOLID}; color: {TEXT_HINT}; }}
    """

def btn_success():
    return f"""
        QPushButton {{
            background: {TEAL};
            color: white;
            border: none;
            border-radius: {RADIUS_SM};
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: #0D6460; }}
        QPushButton:disabled {{ background: {BORDER_SOLID}; color: {TEXT_HINT}; }}
    """

# ── List widget ───────────────────────────────────────────────────────────────
def list_widget():
    return f"""
        QListWidget {{
            border: none;
            background: transparent;
            outline: none;
        }}
        QListWidget::item {{
            padding: 10px 14px;
            border-bottom: 1px solid {BORDER_SOLID};
            border-radius: 0;
            background: {SURFACE};
            color: {TEXT};
        }}
        QListWidget::item:hover {{
            background: {BG};
        }}
        QListWidget::item:selected {{
            background: {ACCENT_BG};
            color: {TEXT};
            border-left: 2px solid {ACCENT};
        }}
    """

# ── Badge helpers ─────────────────────────────────────────────────────────────
def status_badge_style(status: str) -> str:
    fg, bg = STATUS_COLORS.get(status, (TEXT_SEC, BG))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
        f"padding: 2px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.3px; }}"
    )

def role_badge_style(role: str) -> str:
    fg, bg = ROLE_COLORS.get(role, (TEXT_SEC, BG))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
        f"padding: 2px 8px; font-size: 10px; font-weight: 700; }}"
    )

# ── Top bar ───────────────────────────────────────────────────────────────────
def topbar():
    return f"""
        QFrame {{
            background: {SURFACE};
            border: none;
            border-bottom: 1px solid {BORDER_SOLID};
        }}
    """
