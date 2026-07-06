from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QFrame, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from services.firebase_client import FirebaseClient
from utils.logger import logger
import utils.theme as T
from datetime import datetime


def _status_pill_style(status: str) -> str:
    fg, bg = T.STATUS_COLORS.get(status, (T.TEXT_SEC, T.BG))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
        f"padding: 2px 8px; font-size: 10px; font-weight: 700; }}"
    )


class EmployeeDashboard(QWidget):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user      = user
        self.on_logout = on_logout
        self.fb        = FirebaseClient()
        self.current_project_id = None

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
        greeting_lbl = QLabel(f"{greeting}, {user['username']}")
        greeting_lbl.setStyleSheet(f"QLabel {{ font-size: 14px; color: {T.TEXT_SEC}; background: transparent; }}")

        tb.addWidget(brand)
        tb.addWidget(sep)
        tb.addSpacing(12)
        tb.addWidget(greeting_lbl)
        tb.addStretch()

        role_pill = QLabel("Employee")
        role_pill.setStyleSheet(T.role_badge_style("employee"))
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

        # ── Content area ──────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(32, 28, 32, 28)
        content_layout.setSpacing(20)

        # ── LEFT: Projects (35%) ──────────────────────────────────────────────
        left_card = QFrame()
        left_card.setStyleSheet(T.card())
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(14)

        proj_header = QHBoxLayout()
        proj_title = QLabel("Projects")
        proj_title.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent; }}")
        self.proj_count = QLabel("0")
        self.proj_count.setStyleSheet(f"QLabel {{ background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600; }}")
        proj_header.addWidget(proj_title)
        proj_header.addStretch()
        proj_header.addWidget(self.proj_count)
        left_layout.addLayout(proj_header)

        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("Search projects...")
        self.project_search.setStyleSheet(T.input_field_flat())
        self.project_search.setMinimumHeight(36)
        self.project_search.textChanged.connect(self.filter_projects)
        left_layout.addWidget(self.project_search)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(T.list_widget())
        self.project_list.itemClicked.connect(self.load_drawings)
        left_layout.addWidget(self.project_list)

        # ── RIGHT: Drawings (65%) ─────────────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(T.card())
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(14)

        draw_header = QHBoxLayout()
        draw_title = QLabel("Drawings")
        draw_title.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent; }}")
        self.draw_count = QLabel("0")
        self.draw_count.setStyleSheet(f"QLabel {{ background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600; }}")
        draw_header.addWidget(draw_title)
        draw_header.addStretch()
        draw_header.addWidget(self.draw_count)
        right_layout.addLayout(draw_header)

        # Empty state
        self.empty_state = QLabel("Select a project to view its drawings")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet(f"QLabel {{ color: {T.TEXT_HINT}; font-size: 13px; background: transparent; padding: 40px; }}")
        right_layout.addWidget(self.empty_state)

        self.drawing_list = QListWidget()
        self.drawing_list.setStyleSheet(T.list_widget())
        self.drawing_list.itemClicked.connect(self.open_drawing)
        self.drawing_list.hide()
        right_layout.addWidget(self.drawing_list)

        content_layout.addWidget(left_card, 35)
        content_layout.addWidget(right_card, 65)
        main_layout.addWidget(content)

        # ── Auto-refresh ──────────────────────────────────────────────────────
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(3000)

        self.load_projects()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _greeting(self):
        hour = datetime.now().hour
        if hour < 12:  return "Good morning"
        if hour < 17:  return "Good afternoon"
        return "Good evening"

    def _badge_text(self, status: str) -> str:
        mapping = {
            "not_started":    "Not Started",
            "in_progress":    "In Progress",
            "submitted":      "Submitted",
            "admin_approved": "Admin Approved",
            "admin_rejected": "Rejected",
            "client_approved":"Client Approved",
        }
        return mapping.get(status, status.replace("_", " ").title())

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    def auto_refresh(self):
        try:
            if self.current_project_id:
                current_item = self.drawing_list.currentItem()
                current_drawing_id = current_item.data(Qt.UserRole) if current_item else None
                self.refresh_drawings_list()
                if current_drawing_id:
                    for i in range(self.drawing_list.count()):
                        item = self.drawing_list.item(i)
                        if item.data(Qt.UserRole) == current_drawing_id:
                            self.drawing_list.setCurrentItem(item)
                            break
        except Exception as e:
            logger.error(f"Auto-refresh error: {str(e)}")

    def refresh_drawings_list(self):
        if not self.current_project_id:
            return
        try:
            drawings = (
                self.fb.root.child("drawings").child(self.current_project_id).get() or {}
            )
            scroll_pos = self.drawing_list.verticalScrollBar().value()
            self.drawing_list.clear()
            self._populate_drawings(drawings)
            self.drawing_list.verticalScrollBar().setValue(scroll_pos)
        except Exception as e:
            logger.error(f"Error refreshing drawings: {str(e)}")

    # ── Data loading ──────────────────────────────────────────────────────────
    def load_projects(self):
        self.project_list.clear()
        try:
            projects = self.fb.root.child("projects").get() or {}
            count = 0
            for pid, project in projects.items():
                if self.user["user_id"] in project.get("assigned_users", {}):
                    item = QListWidgetItem(f"{project['name']}\n{project['client_name']}")
                    item.setData(Qt.UserRole, pid)
                    self.project_list.addItem(item)
                    count += 1
            self.proj_count.setText(str(count))
            logger.info(f"Loaded {count} projects for user {self.user['user_id']}")
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")

    def filter_projects(self, text):
        text_lower = text.lower()
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def load_drawings(self, item):
        self.drawing_list.clear()
        self.empty_state.hide()
        self.drawing_list.show()
        project_id = item.data(Qt.UserRole)
        self.current_project_id = project_id
        try:
            drawings = (
                self.fb.root.child("drawings").child(project_id).get() or {}
            )
            self._populate_drawings(drawings)
            logger.info(f"Loaded {len(drawings)} drawings for project {project_id}")
        except Exception as e:
            logger.error(f"Error loading drawings: {str(e)}")

    def _populate_drawings(self, drawings: dict):
        """Build drawing list items with status and progress."""
        self.draw_count.setText(str(len(drawings)))
        for did, drawing in drawings.items():
            status  = drawing.get("status", "not_started")
            badge   = self._badge_text(status)
            substeps = drawing.get("sub_steps", {})
            completed = sum(1 for s in substeps.values() if s.get("completed", False))
            total     = len(substeps)
            payment   = " · Paid" if drawing.get("payment_received", False) else ""
            label     = f"{drawing['name']}\n{completed}/{total} steps  ·  {badge}{payment}"
            d_item = QListWidgetItem(label)
            d_item.setData(Qt.UserRole, did)
            self.drawing_list.addItem(d_item)

    def open_drawing(self, item):
        drawing_id   = item.data(Qt.UserRole)
        project_item = self.project_list.currentItem()
        if not project_item:
            return
        project_id = project_item.data(Qt.UserRole)
        mw = self.window()
        if hasattr(mw, "show_drawing_detail"):
            mw.show_drawing_detail(project_id, drawing_id)

    def handle_logout(self):
        try:
            self.refresh_timer.stop()
            self.fb.record_logout_time(self.user["user_id"])
            logger.info(f"User {self.user['user_id']} logged out")
        except Exception as e:
            logger.error(f"Error recording logout: {str(e)}")
        self.on_logout()
