from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QGridLayout, QScrollArea, QDialog, QDateEdit,
    QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate
from services.firebase_client import FirebaseClient
from ui.admin_projects import AdminProjects
from ui.admin_review import AdminReview
from ui.admin_template import AdminTemplate
from ui.superadmin_users import SuperAdminUsers
import utils.theme as T
from datetime import datetime


# ── Date Range Dialog ─────────────────────────────────────────────────────────
class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Report")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setStyleSheet(f"QDialog {{ background: {T.SURFACE}; }} QLabel {{ background: transparent; }}")

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Employee Performance Report")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {T.TEXT};")
        desc = QLabel("Choose a date range or use all available data.")
        desc.setStyleSheet(f"font-size: 13px; color: {T.TEXT_SEC};")

        layout.addWidget(title)
        layout.addWidget(desc)

        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {T.BORDER}; max-height: 1px;")
        layout.addWidget(div)

        self.all_time_checkbox = QCheckBox("Use all available data (ignore date range)")
        self.all_time_checkbox.setStyleSheet(f"""
            QCheckBox {{ font-size: 13px; color: {T.TEXT}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 1.5px solid {T.BORDER_MED}; border-radius: 4px; background: {T.SURFACE}; }}
            QCheckBox::indicator:checked {{ background: {T.ACCENT}; border-color: {T.ACCENT}; }}
        """)
        self.all_time_checkbox.toggled.connect(self.toggle_date_inputs)
        layout.addWidget(self.all_time_checkbox)

        self.date_container = QFrame()
        date_layout = QVBoxLayout(self.date_container)
        date_layout.setSpacing(12)
        date_layout.setContentsMargins(0, 0, 0, 0)

        for label_text, attr in [("Start Date", "start_date"), ("End Date", "end_date")]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC};")
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("MMMM dd, yyyy")
            date_edit.setStyleSheet(f"""
                QDateEdit {{
                    padding: 9px 12px; border: 1.5px solid {T.BORDER};
                    border-radius: {T.RADIUS_SM}; font-size: 13px;
                    background: {T.SURFACE}; color: {T.TEXT};
                }}
                QDateEdit:focus {{ border-color: {T.ACCENT}; }}
                QDateEdit::drop-down {{ border: none; width: 28px; }}
                QDateEdit::down-arrow {{
                    border-left: 4px solid transparent; border-right: 4px solid transparent;
                    border-top: 5px solid {T.TEXT_SEC}; margin-right: 8px;
                }}
            """)
            setattr(self, attr, date_edit)
            date_layout.addWidget(lbl)
            date_layout.addWidget(date_edit)

        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(self.date_container)

        # Quick range buttons
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        ql = QLabel("Quick:")
        ql.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")
        quick_row.addWidget(ql)
        chip_style = f"""
            QPushButton {{
                background: {T.BG}; border: 1px solid {T.BORDER};
                border-radius: 4px; padding: 4px 10px;
                font-size: 11px; color: {T.TEXT_SEC}; font-weight: 600;
            }}
            QPushButton:hover {{ background: {T.BORDER}; color: {T.TEXT}; }}
        """
        for label, days in [("7 days", 7), ("30 days", 30), ("This month", 0)]:
            btn = QPushButton(label)
            btn.setStyleSheet(chip_style)
            btn.setCursor(Qt.PointingHandCursor)
            if days:
                btn.clicked.connect(lambda _, d=days: self.set_quick_range(d))
            else:
                btn.clicked.connect(self.set_this_month)
            quick_row.addWidget(btn)
        quick_row.addStretch()
        layout.addLayout(quick_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Cancel"); cancel.setStyleSheet(T.btn_secondary()); cancel.setCursor(Qt.PointingHandCursor)
        cancel.setMinimumHeight(38); cancel.clicked.connect(self.reject)
        generate = QPushButton("Generate Report"); generate.setStyleSheet(T.btn_primary()); generate.setCursor(Qt.PointingHandCursor)
        generate.setMinimumHeight(38); generate.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(generate)
        layout.addLayout(btn_row)

    def set_quick_range(self, days):
        self.all_time_checkbox.setChecked(False)
        self.end_date.setDate(QDate.currentDate())
        self.start_date.setDate(QDate.currentDate().addDays(-days))

    def set_this_month(self):
        self.all_time_checkbox.setChecked(False)
        today = QDate.currentDate()
        self.start_date.setDate(QDate(today.year(), today.month(), 1))
        self.end_date.setDate(today)

    def toggle_date_inputs(self, checked):
        self.date_container.setEnabled(not checked)

    def get_date_range(self):
        if self.all_time_checkbox.isChecked():
            return None, None
        return (
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )


# ── Nav Card ──────────────────────────────────────────────────────────────────
class NavCard(QFrame):
    clicked = Signal()

    def __init__(self, icon_text, title, description, accent_color, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setCursor(Qt.PointingHandCursor)
        self._normal_style = f"""
            QFrame {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: {T.RADIUS};
            }}
        """
        self._hover_style = f"""
            QFrame {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER_MED};
                border-radius: {T.RADIUS};
            }}
        """
        self.setStyleSheet(self._normal_style)
        self.setFixedHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)

        # Icon bubble
        icon_bubble = QLabel(icon_text)
        icon_bubble.setFixedSize(38, 38)
        icon_bubble.setAlignment(Qt.AlignCenter)
        icon_bubble.setStyleSheet(f"""
            QLabel {{
                background: {accent_color}18;
                color: {accent_color};
                border-radius: 9px;
                font-size: 16px;
                font-weight: 700;
            }}
        """)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"QLabel {{ font-size: 14px; font-weight: 700; color: {T.TEXT}; background: transparent; }}")

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"QLabel {{ font-size: 12px; color: {T.TEXT_SEC}; background: transparent; }}")
        desc_lbl.setWordWrap(True)

        layout.addWidget(icon_bubble)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._normal_style)
        super().leaveEvent(event)


# ── Admin Dashboard ───────────────────────────────────────────────────────────
class AdminDashboard(QWidget):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user      = user
        self.on_logout = on_logout

        self.setStyleSheet(T.app_base())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(64)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border: none;
                border-bottom: 1px solid {T.BORDER};
            }}
        """)
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(32, 0, 32, 0)

        brand = QLabel("SOT")
        brand.setStyleSheet(f"QLabel {{ font-size: 18px; font-weight: 800; color: {T.ACCENT}; background: transparent; }}")

        sep = QFrame(); sep.setFixedSize(1, 24)
        sep.setStyleSheet(f"background: {T.BORDER}; border: none;")

        greeting = self._greeting()
        page_title = QLabel(f"{greeting}, {user['username']}")
        page_title.setStyleSheet(f"QLabel {{ font-size: 14px; color: {T.TEXT_SEC}; background: transparent; }}")

        tb.addWidget(brand)
        tb.addWidget(sep)
        tb.addSpacing(12)
        tb.addWidget(page_title)
        tb.addStretch()

        # Role pill
        role = user.get("role", "employee")
        fg, bg = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
        role_pill = QLabel(role.replace("_", " ").title())
        role_pill.setStyleSheet(f"""
            QLabel {{
                background: {bg}; color: {fg};
                border-radius: 4px; padding: 3px 10px;
                font-size: 11px; font-weight: 700;
            }}
        """)
        tb.addWidget(role_pill)
        tb.addSpacing(16)

        logout_btn = QPushButton("Sign out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(32)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T.TEXT_SEC};
                border: 1px solid {T.BORDER}; border-radius: 5px;
                font-size: 12px; font-weight: 600; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {T.BG}; color: {T.TEXT}; }}
        """)
        logout_btn.clicked.connect(self.handle_logout)
        tb.addWidget(logout_btn)
        main_layout.addWidget(top_bar)

        # ── Scrollable content ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {T.BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 36, 40, 40)
        cl.setSpacing(28)

        # Section heading
        heading_row = QHBoxLayout()
        heading = QLabel("Dashboard")
        heading.setStyleSheet(f"QLabel {{ font-size: 22px; font-weight: 700; color: {T.TEXT}; background: transparent; }}")
        sub = QLabel("Select a section to get started")
        sub.setStyleSheet(f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; background: transparent; }}")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        cl.addLayout(heading_row)
        cl.addWidget(sub)

        # ── Navigation cards ──────────────────────────────────────────────────
        section_lbl = QLabel("MANAGEMENT")
        section_lbl.setStyleSheet(f"QLabel {{ font-size: 11px; font-weight: 700; color: {T.TEXT_HINT}; background: transparent; letter-spacing: 1px; }}")
        cl.addWidget(section_lbl)

        grid = QGridLayout()
        grid.setSpacing(16)

        cards = [
            ("P", "Projects",       "Create, assign and manage all projects",       T.ACCENT,   self.open_projects),
            ("R", "Review Drawings","Approve or reject submitted drawings",          "#7C3AED",  self.open_review),
            ("E", "Employee Report","Download login/logout & hours report",          T.SUCCESS,  self.download_employee_report),
            ("S", "Project Report", "Status overview with payment tracking",         "#0891B2",  self.download_project_report),
        ]

        if self.user["role"] == "super_admin":
            cards += [
                ("U", "Users",        "Create and manage user accounts",            "#D97706",  self.open_users),
                ("T", "Template",     "Edit the default drawing template",          "#DC2626",  self.open_template),
            ]

        cols = 3
        for i, (icon, title, desc, color, fn) in enumerate(cards):
            card = NavCard(icon, title, desc, color)
            card.clicked.connect(fn)
            grid.addWidget(card, i // cols, i % cols)

        cl.addLayout(grid)
        cl.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Hidden stack kept for compatibility (pages are loaded lazily in MainWindow)
        self.pages = None

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _greeting(self):
        hour = datetime.now().hour
        if hour < 12:  return "Good morning"
        if hour < 17:  return "Good afternoon"
        return "Good evening"

    # ── Actions ───────────────────────────────────────────────────────────────
    def handle_logout(self):
        fb = FirebaseClient()
        fb.record_logout_time(self.user["user_id"])
        self.on_logout()

    def open_projects(self):
        mw = self.window()
        if hasattr(mw, "show_projects"): mw.show_projects()

    def open_review(self):
        mw = self.window()
        if hasattr(mw, "show_review"): mw.show_review()

    def open_template(self):
        mw = self.window()
        if hasattr(mw, "show_templates"): mw.show_templates()

    def open_users(self):
        mw = self.window()
        if hasattr(mw, "show_users"): mw.show_users()

    def download_employee_report(self):
        from utils.modern_dialogs import ModernMessageBox
        try:
            dialog = DateRangeDialog(self)
            if dialog.exec() == QDialog.Accepted:
                start_date, end_date = dialog.get_date_range()
                from services.employee_performance_report import generate_employee_performance_report
                file = generate_employee_performance_report(start_date, end_date)
                date_info = f"\nRange: {start_date} → {end_date}" if (start_date and end_date) else "\nAll time data"
                ModernMessageBox.success(self, "Report Ready", f"Employee report saved.{date_info}\n\n{file}")
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to generate report: {str(e)}")

    def download_project_report(self):
        from utils.modern_dialogs import ModernMessageBox
        try:
            from services.project_status_report import generate_project_status_report
            file = generate_project_status_report()
            ModernMessageBox.success(self, "Report Ready", f"Project status report saved.\n\n{file}")
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to generate report: {str(e)}")
