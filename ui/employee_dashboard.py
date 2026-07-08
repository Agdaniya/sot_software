from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QFrame, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from services.firebase_client import FirebaseClient
from utils.logger import logger
import utils.theme as T
from datetime import datetime


# ── Status pill colours (matches admin_review.py) ─────────────────────────────
_STATUS_META = {
    "submitted":       ("Submitted",       "#ede9fe", "#5b21b6"),
    "client_approved": ("Client Approved", "#ccfbf1", "#0f766e"),
    "admin_approved":  ("Admin Approved",  "#ccfbf1", "#0f766e"),
    "in_progress":     ("In Progress",     "#fef9c3", "#92400e"),
    "not_started":     ("Not Started",     "#f3f4f6", "#6b7280"),
    "admin_rejected":  ("Rejected",        "#ffe4e6", "#be123c"),
    "rejected":        ("Rejected",        "#ffe4e6", "#be123c"),
    "completed":       ("Completed",       "#ccfbf1", "#0f766e"),
}


def _status_pill(status: str) -> tuple:
    return _STATUS_META.get(status, ("Unknown", "#f3f4f6", "#6b7280"))


# ── Custom drawing row widget ─────────────────────────────────────────────────
class DrawingRowWidget(QWidget):
    def __init__(self, name: str, status: str, done: int, total: int,
                 paid: bool, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        label, pill_bg, pill_fg = _status_pill(status)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        # Left: name + steps
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setContentsMargins(0, 0, 0, 0)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {T.TEXT};"
        )
        text_col.addWidget(name_lbl)

        steps_lbl = QLabel(f"{done}/{total} steps complete")
        steps_lbl.setStyleSheet(
            f"font-size: 12px; color: {T.TEXT_SEC}; "
            f"font-family: 'Courier New', monospace;"
        )
        text_col.addWidget(steps_lbl)
        outer.addLayout(text_col, 1)

        # PAID badge
        if paid:
            paid_lbl = QLabel("PAID")
            paid_lbl.setStyleSheet(
                "font-size: 10px; font-weight: 700; padding: 2px 8px; "
                "border-radius: 4px; background: #ccfbf1; color: #0f766e; "
                "font-family: 'Courier New', monospace; letter-spacing: 0.5px;"
            )
            outer.addWidget(paid_lbl)

        # Status pill
        pill = QLabel(f"● {label}")
        pill.setAlignment(Qt.AlignCenter)
        pill.setStyleSheet(
            f"font-size: 11px; font-weight: 600; padding: 3px 12px; "
            f"border-radius: 10px; background: {pill_bg}; color: {pill_fg}; "
            f"font-family: 'Courier New', monospace;"
        )
        outer.addWidget(pill)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")


# ── Custom project row widget ─────────────────────────────────────────────────
class ProjectRowWidget(QWidget):
    def __init__(self, name: str, client: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(3)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {T.TEXT};"
        )
        outer.addWidget(name_lbl)

        client_lbl = QLabel(client)
        client_lbl.setStyleSheet(
            f"font-size: 12px; color: {T.TEXT_SEC};"
        )
        outer.addWidget(client_lbl)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")


# ── Employee Dashboard ────────────────────────────────────────────────────────
class EmployeeDashboard(QWidget):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user      = user
        self.on_logout = on_logout
        self.fb        = FirebaseClient()
        self.current_project_id = None
        self._all_projects = {}

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
        left_panel.setFixedWidth(340)
        left_panel.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Panel header
        proj_header = QFrame()
        proj_header.setFixedHeight(56)
        proj_header.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        ph = QHBoxLayout(proj_header)
        ph.setContentsMargins(20, 0, 20, 0)
        ph.setSpacing(8)

        proj_title = QLabel("Projects")
        proj_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        self.proj_count = QLabel("0")
        self.proj_count.setStyleSheet(
            f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        ph.addWidget(proj_title)
        ph.addWidget(self.proj_count)
        ph.addStretch()
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
        self.project_list.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{ border: none; margin: 0; padding: 0; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: #f0f6ff; "
            f"border-left: 3px solid #3b82f6; }}"
        )
        self.project_list.setSpacing(0)
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
        draw_header.setFixedHeight(56)
        draw_header.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        dh = QHBoxLayout(draw_header)
        dh.setContentsMargins(20, 0, 20, 0)
        dh.setSpacing(8)

        draw_title = QLabel("Drawings")
        draw_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        self.draw_count = QLabel("")
        self.draw_count.setStyleSheet(
            f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        self.draw_count.hide()
        dh.addWidget(draw_title)
        dh.addWidget(self.draw_count)
        dh.addStretch()
        right_layout.addWidget(draw_header)

        # Empty state
        self.empty_state = QLabel("Select a project to view its drawings")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet(
            f"color: {T.TEXT_HINT}; font-size: 13px; padding: 60px;"
        )
        right_layout.addWidget(self.empty_state)

        self.drawing_list = QListWidget()
        self.drawing_list.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{ border: none; margin: 0; padding: 0; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: #f0f6ff; "
            f"border-left: 3px solid #3b82f6; }}"
        )
        self.drawing_list.setSpacing(0)
        self.drawing_list.itemClicked.connect(self.open_drawing)
        self.drawing_list.hide()
        right_layout.addWidget(self.drawing_list, 1)

        body_layout.addWidget(left_panel)
        body_layout.addWidget(right_panel, 1)
        main_layout.addWidget(body, 1)

        # Auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(3000)

        self.load_projects()

    # ── Helpers ───────────────────────────────────────────────────────────────
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
        self._all_projects = {}
        try:
            projects = self.fb.root.child("projects").get() or {}
            count = 0
            for pid, project in projects.items():
                if self.user["user_id"] in project.get("assigned_users", {}):
                    self._all_projects[pid] = project
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, pid)
                    item.setData(Qt.UserRole + 1, {
                        "name": project.get("name", ""),
                        "client": project.get("client_name", ""),
                    })
                    w = ProjectRowWidget(
                        project.get("name", ""),
                        project.get("client_name", ""),
                    )
                    hint = w.sizeHint()
                    item.setSizeHint(QSize(hint.width(), max(hint.height(), 64)))
                    self.project_list.addItem(item)
                    self.project_list.setItemWidget(item, w)
                    count += 1
            self.proj_count.setText(str(count))
            self.proj_count.setVisible(count > 0)
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")

    def filter_projects(self, text):
        lo = text.lower()
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            d = item.data(Qt.UserRole + 1) or {}
            visible = lo in d.get("name", "").lower() or lo in d.get("client", "").lower()
            item.setHidden(not visible)

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
        count = len(drawings)
        self.draw_count.setText(str(count))
        self.draw_count.setVisible(count > 0)

        for did, drawing in drawings.items():
            status   = drawing.get("status", "not_started")
            substeps = drawing.get("sub_steps", {})
            done     = sum(1 for s in substeps.values() if s.get("completed", False))
            total    = len(substeps)
            paid     = drawing.get("payment_received", False)

            d_item = QListWidgetItem()
            d_item.setData(Qt.UserRole, did)
            d_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            w = DrawingRowWidget(drawing.get("name", "Unnamed"), status, done, total, paid)
            hint = w.sizeHint()
            d_item.setSizeHint(QSize(hint.width(), max(hint.height(), 68)))
            self.drawing_list.addItem(d_item)
            self.drawing_list.setItemWidget(d_item, w)

    def open_drawing(self, item):
        drawing_id   = item.data(Qt.UserRole)
        project_item = self.project_list.currentItem()
        if not project_item:
            return
        project_id = project_item.data(Qt.UserRole)
        mw = self.window()
        if hasattr(mw, "show_drawing_detail"):
            mw.show_drawing_detail(project_id, drawing_id)
