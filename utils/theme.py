"""
SOT Design System — aligned with SOT React design
Single source of truth for every colour, radius, and shared stylesheet.
"""

# ── Palette ───────────────────────────────────────────────────────────────────
BG           = "#F7F8FA"       # page background (light gray)
SURFACE      = "#FFFFFF"       # card / panel surface
BORDER_SOLID = "#E5E7EB"       # borders
BORDER       = "#E5E7EB"       # alias

TEXT         = "#0f172a"       # primary text  (very dark navy)
TEXT_SEC     = "#64748b"       # secondary / muted
TEXT_HINT    = "#94a3b8"       # placeholder

# Navy primary — matches the dark navy seen in login panel & buttons
ACCENT       = "#1e2a3a"       # primary button, left panel background
ACCENT_DARK  = "#152030"       # hover
ACCENT_BG    = "#e8edf3"       # tint for selected rows

SUCCESS      = "#0f766e"       # teal-700
SUCCESS_BG   = "#f0fdfa"
WARNING      = "#d97706"       # amber-600
WARNING_BG   = "#fffbeb"
DANGER       = "#dc2626"       # red-600
DANGER_BG    = "#fef2f2"
DANGER_DARK  = "#b91c1c"

TEAL         = "#0f766e"
TEAL_BG      = "#f0fdfa"
TEAL_DARK    = "#0d6460"

INDIGO       = "#4f46e5"
INDIGO_BG    = "#eef2ff"

RADIUS       = "10px"
RADIUS_SM    = "6px"
RADIUS_LG    = "12px"
RADIUS_XL    = "16px"

FONT         = "'Segoe UI', 'Inter', 'Arial', sans-serif"

# ── Role badge colours ────────────────────────────────────────────────────────
ROLE_COLORS = {
    "super_admin": ("#1d4ed8", "#dbeafe"),   # blue
    "admin":       ("#7c3aed", "#ede9fe"),   # violet
    "employee":    ("#374151", "#f3f4f6"),   # gray
}

# ── Status colours ────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "not_started":     ("#6b7280", "#f3f4f6"),
    "in_progress":     ("#b45309", "#fef3c7"),
    "submitted":       ("#4f46e5", "#eef2ff"),
    "admin_approved":  ("#0f766e", "#f0fdfa"),
    "admin_rejected":  ("#dc2626", "#fef2f2"),
    "client_approved": ("#0f766e", "#f0fdfa"),
    "rejected":        ("#dc2626", "#fef2f2"),
    "completed":       ("#0f766e", "#f0fdfa"),
}

STATUS_DOT = {
    "not_started":     "#9ca3af",
    "in_progress":     "#f59e0b",
    "submitted":       "#4f46e5",
    "admin_approved":  "#0f766e",
    "admin_rejected":  "#dc2626",
    "client_approved": "#0f766e",
    "rejected":        "#dc2626",
    "completed":       "#0f766e",
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
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.1px;
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
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background: {BG};
            border-color: #c0c4cc;
        }}
        QPushButton:disabled {{ color: {TEXT_HINT}; }}
    """

def btn_danger():
    return f"""
        QPushButton {{
            background: {SURFACE};
            color: {DANGER};
            border: 1px solid #fecaca;
            border-radius: {RADIUS_SM};
            padding: 9px 18px;
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
            padding: 9px 18px;
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
            padding: 9px 18px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {TEAL_DARK}; }}
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
