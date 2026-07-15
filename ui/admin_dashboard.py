from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QGridLayout, QScrollArea, QDialog, QDateEdit,
    QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate
from services.firebase_client import FirebaseClient
import utils.theme as T
from datetime import datetime


# ── Shared top-bar builder (reused by all dashboard screens) ──────────────────
def make_topbar(parent_widget, user, on_logout, show_back=False, back_title=""):
    """Returns a (topbar_frame, back_btn_or_None) tuple."""
    bar = QFrame()
    bar.setFixedHeight(56)
    bar.setStyleSheet(T.topbar())

    h = QHBoxLayout(bar)
    h.setContentsMargins(24, 0, 24, 0)
    h.setSpacing(0)

    back_btn = None
    if show_back:
        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedHeight(30)
        back_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {T.TEXT_SEC}; "
            f"border: 1px solid {T.BORDER_SOLID}; border-radius: {T.RADIUS_SM}; "
            f"font-size: 12px; font-weight: 600; padding: 0 12px; }}"
            f"QPushButton:hover {{ background: {T.BG}; color: {T.TEXT}; }}"
        )
        h.addWidget(back_btn)

        sep = QFrame()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        h.addSpacing(12)
        h.addWidget(sep)
        h.addSpacing(12)

        title_lbl = QLabel(back_title)
        title_lbl.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        h.addWidget(title_lbl)
        h.addStretch()
    else:
        brand = QLabel("SOT")
        brand.setStyleSheet(
            f"QLabel {{ font-size: 15px; font-weight: 800; color: {T.TEXT}; "
            f"letter-spacing: -0.5px; background: transparent; }}"
        )
        sep = QFrame()
        sep.setFixedSize(1, 18)
        sep.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")

        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        first = user.get("username", "").split()[0] if user else ""
        greeting_lbl = QLabel(f"{greet}, <b>{first}</b>")
        greeting_lbl.setTextFormat(Qt.RichText)
        greeting_lbl.setStyleSheet(
            f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; background: transparent; }}"
        )

        h.addWidget(brand)
        h.addSpacing(12)
        h.addWidget(sep)
        h.addSpacing(12)
        h.addWidget(greeting_lbl)
        h.addStretch()

    # Role badge
    if user:
        role = user.get("role", "employee")
        fg, bg = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
        role_lbl = QLabel(role.replace("_", " ").title())
        role_lbl.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
            f"padding: 2px 8px; font-size: 10px; font-weight: 700; }}"
        )
        h.addWidget(role_lbl)
        h.addSpacing(14)

    if on_logout:
        logout_btn = QPushButton("⇥  Sign out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(30)
        logout_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {T.TEXT_SEC}; "
            f"border: 1px solid {T.BORDER_SOLID}; border-radius: {T.RADIUS_SM}; "
            f"font-size: 12px; font-weight: 600; padding: 0 12px; }}"
            f"QPushButton:hover {{ background: {T.BG}; color: {T.TEXT}; }}"
        )
        logout_btn.clicked.connect(on_logout)
        h.addWidget(logout_btn)

    return bar, back_btn


# ── Date Range Dialog ─────────────────────────────────────────────────────────
class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Report")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(
            f"QDialog {{ background: {T.SURFACE}; }} "
            f"QLabel {{ background: transparent; }}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Employee Performance Report")
        title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {T.TEXT};"
        )
        desc = QLabel("Choose a date range or use all available data.")
        desc.setStyleSheet(f"font-size: 13px; color: {T.TEXT_SEC};")

        layout.addWidget(title)
        layout.addWidget(desc)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        layout.addWidget(div)

        self.all_time_checkbox = QCheckBox("Use all available data (ignore date range)")
        self.all_time_checkbox.setStyleSheet(
            f"QCheckBox {{ font-size: 13px; color: {T.TEXT}; spacing: 8px; }}"
            f"QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: 4px; background: {T.SURFACE}; }}"
            f"QCheckBox::indicator:checked {{ background: {T.ACCENT}; border-color: {T.ACCENT}; }}"
        )
        self.all_time_checkbox.toggled.connect(self.toggle_date_inputs)
        layout.addWidget(self.all_time_checkbox)

        self.date_container = QFrame()
        date_layout = QVBoxLayout(self.date_container)
        date_layout.setSpacing(10)
        date_layout.setContentsMargins(0, 0, 0, 0)

        lbl_style = f"font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; letter-spacing: 0.4px;"
        date_style = (
            f"QDateEdit {{ padding: 8px 12px; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; font-size: 13px; "
            f"background: {T.SURFACE}; color: {T.TEXT}; }}"
            f"QDateEdit:focus {{ border-color: {T.ACCENT}; }}"
            f"QDateEdit::drop-down {{ border: none; width: 26px; }}"
            f"QDateEdit::down-arrow {{ border-left: 4px solid transparent; "
            f"border-right: 4px solid transparent; border-top: 5px solid {T.TEXT_SEC}; "
            f"margin-right: 8px; }}"
        )
        for label_text, attr in [("Start Date", "start_date"), ("End Date", "end_date")]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(lbl_style)
            de = QDateEdit()
            de.setCalendarPopup(True)
            de.setDisplayFormat("MMMM dd, yyyy")
            de.setStyleSheet(date_style)
            setattr(self, attr, de)
            date_layout.addWidget(lbl)
            date_layout.addWidget(de)

        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(self.date_container)

        # Quick range chips
        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        ql = QLabel("Quick:")
        ql.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")
        quick_row.addWidget(ql)
        chip = (
            f"QPushButton {{ background: {T.BG}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: 4px; padding: 3px 10px; font-size: 11px; "
            f"color: {T.TEXT_SEC}; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {T.BORDER_SOLID}; color: {T.TEXT}; }}"
        )
        for label, days in [("7 days", 7), ("30 days", 30), ("This month", 0)]:
            btn = QPushButton(label)
            btn.setStyleSheet(chip)
            btn.setCursor(Qt.PointingHandCursor)
            if days:
                btn.clicked.connect(lambda _, d=days: self.set_quick_range(d))
            else:
                btn.clicked.connect(self.set_this_month)
            quick_row.addWidget(btn)
        quick_row.addStretch()
        layout.addLayout(quick_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(T.btn_secondary())
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setMinimumHeight(38)
        cancel.clicked.connect(self.reject)
        generate = QPushButton("Generate Report")
        generate.setStyleSheet(T.btn_primary())
        generate.setCursor(Qt.PointingHandCursor)
        generate.setMinimumHeight(38)
        generate.clicked.connect(self.accept)
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
            self.end_date.date().toString("yyyy-MM-dd"),
        )


# ── Nav Card ──────────────────────────────────────────────────────────────────
class NavCard(QFrame):
    clicked = Signal()

    def __init__(self, abbr, title, description, accent_color, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setCursor(Qt.PointingHandCursor)
        self._normal = (
            f"QFrame {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS}; }}"
        )
        self._hover = (
            f"QFrame {{ background: {T.BG}; border: 1px solid #C0C0C8; "
            f"border-radius: {T.RADIUS}; }}"
        )
        self.setStyleSheet(self._normal)
        self.setFixedHeight(148)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Abbr bubble — solid filled square with white text
        bubble = QLabel(abbr)
        bubble.setFixedSize(44, 44)
        bubble.setAlignment(Qt.AlignCenter)
        bubble.setStyleSheet(
            f"QLabel {{ background: {accent_color}; color: white; "
            f"border: none; "
            f"border-radius: 10px; font-size: 12px; font-weight: 700; }}"
        )

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"QLabel {{ font-size: 14px; font-weight: 700; color: {T.TEXT}; background: transparent; border: none; }}"
        )

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            f"QLabel {{ font-size: 12px; color: {T.TEXT_SEC}; background: transparent; border: none; }}"
        )
        desc_lbl.setWordWrap(True)

        layout.addWidget(bubble)
        layout.addSpacing(2)
        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._normal)
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

        topbar, _ = make_topbar(self, user, self._handle_logout)
        main_layout.addWidget(topbar)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {T.BG}; }}"
        )

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 32, 40, 40)
        cl.setSpacing(24)

        # Heading
        heading = QLabel("Dashboard")
        heading.setStyleSheet(
            f"QLabel {{ font-size: 20px; font-weight: 600; color: {T.TEXT}; "
            f"background: transparent; letter-spacing: -0.3px; }}"
        )
        sub = QLabel("Select a section to get started.")
        sub.setStyleSheet(
            f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; background: transparent; }}"
        )
        cl.addWidget(heading)
        cl.addWidget(sub)

        # Section label
        section_lbl = QLabel("MANAGEMENT")
        section_lbl.setStyleSheet(
            f"QLabel {{ font-size: 10px; font-weight: 700; color: {T.TEXT_HINT}; "
            f"background: transparent; letter-spacing: 1.5px; }}"
        )
        cl.addWidget(section_lbl)

        # Cards grid
        grid = QGridLayout()
        grid.setSpacing(12)

        cards = [
            ("PR", "Projects",        "Create and manage projects, assign team members.",              "#4f46e5",  self.open_projects),
            ("RD", "Review Drawings", "Review submitted drawings — approve or reject with feedback.",  "#7c3aed",  self.open_review),
            ("TK", "Tasks",           "Assign ad-hoc tasks to employees and track progress.",          "#0891b2",  self.open_tasks),
            ("ER", "Employee Report", "Export a date-range Excel report of employee activity.",        "#d97706",  self.download_employee_report),
            ("PR", "Project Report",  "Download an Excel summary of all projects and drawing statuses.", "#0f766e", self.download_project_report),
        ]

        if self.user["role"] == "super_admin":
            cards += [
                ("US", "Users",    "Create and manage user accounts.",         "#d97706", self.open_users),
                ("TM", "Template", "Edit the default drawing template.",        "#dc2626", self.open_template),
            ]

        cols = 3
        for i, (abbr, title, desc, color, fn) in enumerate(cards):
            card = NavCard(abbr, title, desc, color)
            card.clicked.connect(fn)
            grid.addWidget(card, i // cols, i % cols)

        cl.addLayout(grid)
        cl.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _handle_logout(self):
        fb = FirebaseClient()
        fb.record_logout_time(self.user["user_id"])
        self.on_logout()

    def open_projects(self):
        mw = self.window()
        if hasattr(mw, "show_projects"): mw.show_projects()

    def open_review(self):
        mw = self.window()
        if hasattr(mw, "show_review"): mw.show_review()

    def open_tasks(self):
        mw = self.window()
        if hasattr(mw, "show_tasks"): mw.show_tasks()

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
                date_info = (
                    f"\nRange: {start_date} → {end_date}"
                    if (start_date and end_date) else "\nAll time data"
                )
                ModernMessageBox.success(
                    self, "Report Ready",
                    f"Employee report saved.{date_info}\n\n{file}"
                )
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to generate report: {str(e)}")

    def download_project_report(self):
        from utils.modern_dialogs import ModernMessageBox
        try:
            from services.project_status_report import generate_project_status_report
            file = generate_project_status_report()
            ModernMessageBox.success(
                self, "Report Ready",
                f"Project status report saved.\n\n{file}"
            )
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to generate report: {str(e)}")
