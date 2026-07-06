from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QFrame, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from services.firebase_client import FirebaseClient
from utils.logger import logger
import utils.theme as T
from datetime import datetime


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
        from ui.admin_dashboard import make_topbar
        topbar, _ = make_topbar(self, user, self._handle_logout)
        main_layout.addWidget(topbar)

        # ── Two-panel content area ─────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── LEFT: Projects ────────────────────────────────────────────────────
        left_panel = QFrame()
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Panel header
        proj_header = QFrame()
        proj_header.setFixedHeight(52)
        proj_header.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        ph = QHBoxLayout(proj_header)
        ph.setContentsMargins(16, 0, 16, 0)

        proj_title = QLabel("Projects")
        proj_title.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        self.proj_count = QLabel("0")
        self.proj_count.setStyleSheet(
            f"QLabel {{ background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 1px 7px; font-size: 11px; font-weight: 600; font-family: monospace; }}"
        )
        ph.addWidget(proj_title)
        ph.addStretch()
        ph.addWidget(self.proj_count)
        left_layout.addWidget(proj_header)

        # Search box
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        sf = QVBoxLayout(search_frame)
        sf.setContentsMargins(12, 10, 12, 10)
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("Search projects…")
        self.project_search.setMinimumHeight(34)
        self.project_search.setStyleSheet(T.input_field_flat())
        self.project_search.textChanged.connect(self.filter_projects)
        sf.addWidget(self.project_search)
        left_layout.addWidget(search_frame)

        # Project list
        self.project_list = QListWidget()
        self.project_list.setStyleSheet(T.list_widget())
        self.project_list.itemClicked.connect(self.load_drawings)
        left_layout.addWidget(self.project_list)

        # ── RIGHT: Drawings ───────────────────────────────────────────────────
        right_panel = QFrame()
        right_panel.setStyleSheet(
            f"QFrame {{ background: {T.BG}; border: none; }}"
        )
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        draw_header = QFrame()
        draw_header.setFixedHeight(52)
        draw_header.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        dh = QHBoxLayout(draw_header)
        dh.setContentsMargins(16, 0, 16, 0)

        draw_title = QLabel("Drawings")
        draw_title.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        self.draw_count = QLabel("")
        self.draw_count.setStyleSheet(
            f"QLabel {{ background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 1px 7px; font-size: 11px; font-weight: 600; font-family: monospace; }}"
        )
        dh.addWidget(draw_title)
        dh.addStretch()
        dh.addWidget(self.draw_count)
        right_layout.addWidget(draw_header)

        # Empty state
        self.empty_state = QLabel("Select a project to view its drawings")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet(
            f"QLabel {{ color: {T.TEXT_HINT}; font-size: 13px; background: transparent; padding: 60px; }}"
        )
        right_layout.addWidget(self.empty_state)

        self.drawing_list = QListWidget()
        self.drawing_list.setStyleSheet(T.list_widget())
        self.drawing_list.itemClicked.connect(self.open_drawing)
        self.drawing_list.hide()
        right_layout.addWidget(self.drawing_list)

        body_layout.addWidget(left_panel)
        body_layout.addWidget(right_panel, 1)
        main_layout.addWidget(body, 1)

        # Auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(3000)

        self.load_projects()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _badge_text(self, status: str) -> str:
        return T.STATUS_LABELS.get(status, status.replace("_", " ").title())

    def _handle_logout(self):
        try:
            self.refresh_timer.stop()
            self.fb.record_logout_time(self.user["user_id"])
            logger.info(f"User {self.user['user_id']} logged out")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
        self.on_logout()

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    def auto_refresh(self):
        try:
            if self.current_project_id:
                cur = self.drawing_list.currentItem()
                cur_id = cur.data(Qt.UserRole) if cur else None
                self.refresh_drawings_list()
                if cur_id:
                    for i in range(self.drawing_list.count()):
                        if self.drawing_list.item(i).data(Qt.UserRole) == cur_id:
                            self.drawing_list.setCurrentRow(i)
                            break
        except Exception as e:
            logger.error(f"Auto-refresh error: {str(e)}")

    def refresh_drawings_list(self):
        if not self.current_project_id:
            return
        try:
            drawings = self.fb.root.child("drawings").child(self.current_project_id).get() or {}
            pos = self.drawing_list.verticalScrollBar().value()
            self.drawing_list.clear()
            self._populate_drawings(drawings)
            self.drawing_list.verticalScrollBar().setValue(pos)
        except Exception as e:
            logger.error(f"Error refreshing drawings: {str(e)}")

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_projects(self):
        self.project_list.clear()
        try:
            projects = self.fb.root.child("projects").get() or {}
            count = 0
            for pid, project in projects.items():
                if self.user["user_id"] in project.get("assigned_users", {}):
                    item = QListWidgetItem(
                        f"{project['name']}\n{project['client_name']}"
                    )
                    item.setData(Qt.UserRole, pid)
                    self.project_list.addItem(item)
                    count += 1
            self.proj_count.setText(str(count))
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")

    def filter_projects(self, text):
        lo = text.lower()
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setHidden(lo not in item.text().lower())

    def load_drawings(self, item):
        self.drawing_list.clear()
        self.empty_state.hide()
        self.drawing_list.show()
        project_id = item.data(Qt.UserRole)
        self.current_project_id = project_id
        try:
            drawings = self.fb.root.child("drawings").child(project_id).get() or {}
            self._populate_drawings(drawings)
        except Exception as e:
            logger.error(f"Error loading drawings: {str(e)}")

    def _populate_drawings(self, drawings: dict):
        self.draw_count.setText(str(len(drawings)))
        for did, drawing in drawings.items():
            status   = drawing.get("status", "not_started")
            badge    = self._badge_text(status)
            substeps = drawing.get("sub_steps", {})
            done     = sum(1 for s in substeps.values() if s.get("completed", False))
            total    = len(substeps)
            paid_tag = "  · PAID" if drawing.get("payment_received", False) else ""
            label    = f"{drawing['name']}\n{done}/{total} steps  ·  {badge}{paid_tag}"
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
