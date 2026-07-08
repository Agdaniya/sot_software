from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QCheckBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QResizeEvent
from services.firebase_client import FirebaseClient
from core.projects import ProjectManager
from core.auth import User
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import utils.theme as T
import uuid


class AdminProjects(QWidget):
    # ── Responsive sizing bounds ────────────────────────────────────────────
    # Instead of one fixed pixel width/height, the sidebar and employee list
    # scale with the window size but are clamped so they never look cramped
    # on a small laptop or absurdly stretched on a large monitor.
    SIDEBAR_MIN_W   = 220
    SIDEBAR_MAX_W   = 340
    SIDEBAR_RATIO   = 0.22   # ~22% of window width

    EMP_LIST_MIN_H  = 160
    EMP_LIST_MAX_H  = 320
    EMP_LIST_RATIO  = 0.30   # ~30% of window height

    BASE_WINDOW_W   = 1440   # reference width used to derive the font scale
    FONT_SCALE_MIN  = 0.85
    FONT_SCALE_MAX  = 1.25

    LIST_ITEM_MIN_H = 72     # safety net only — real spacing now comes from
                             # the item widget's own margins, not this value

    def __init__(self, current_user=None):
        super().__init__()
        self.current_user        = current_user
        self.fb                  = FirebaseClient()
        self.project_manager     = ProjectManager(self.fb)
        self.selected_project_id = None

        self.setStyleSheet(T.app_base())
        self.setMinimumSize(760, 480)

        from ui.admin_dashboard import make_topbar
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar, back_btn = make_topbar(
            self, current_user, None, show_back=True, back_title="Project Management"
        )
        if back_btn:
            back_btn.clicked.connect(self._go_back)
        root_layout.addWidget(topbar)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── LEFT panel ────────────────────────────────────────────────────────
        left_panel = QFrame()
        left_panel.setMinimumWidth(self.SIDEBAR_MIN_W)
        left_panel.setMaximumWidth(self.SIDEBAR_MAX_W)
        left_panel.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        self.left_panel = left_panel  # kept for resizeEvent
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)

        # List header
        list_header = QFrame()
        list_header.setFixedHeight(56)
        list_header.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        lh = QHBoxLayout(list_header)
        lh.setContentsMargins(20, 0, 16, 0)
        lh.setSpacing(8)
        lh_title = QLabel("Projects")
        lh_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        self.project_count_lbl = QLabel("0")
        self.project_count_lbl.setStyleSheet(
            f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        lh.addWidget(lh_title)
        lh.addWidget(self.project_count_lbl)
        lh.addStretch()
        left.addWidget(list_header)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{ padding: 0px; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; background: {T.SURFACE}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: #f0f6ff; "
            f"border-left: 3px solid #3b82f6; }}"
        )
        self.project_list.itemClicked.connect(self.load_project_data)
        left.addWidget(self.project_list)

        # ── RIGHT panel ───────────────────────────────────────────────────────
        right_outer = QScrollArea()
        right_outer.setWidgetResizable(True)
        right_outer.setStyleSheet(
            f"QScrollArea {{ border: none; background: {T.BG}; }}"
        )

        right_card = QFrame()
        right_card.setStyleSheet(f"QFrame {{ background: {T.BG}; border: none; }}")
        right_outer.setWidget(right_card)

        right = QVBoxLayout(right_card)
        right.setContentsMargins(24, 20, 24, 20)
        right.setSpacing(0)

        # Form header row
        header_row = QHBoxLayout()
        self.right_title = QLabel("New Project")
        self.right_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        new_btn = QPushButton("+ New Project")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setFixedHeight(34)
        new_btn.setStyleSheet(
            f"QPushButton {{ background: {T.SURFACE}; color: {T.TEXT}; "
            f"border: 1px solid {T.BORDER_SOLID}; border-radius: {T.RADIUS_SM}; "
            f"font-size: 12px; font-weight: 600; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: {T.BG}; border-color: #c0c4cc; }}"
        )
        new_btn.clicked.connect(self.create_new_project)
        header_row.addWidget(self.right_title)
        header_row.addStretch()
        header_row.addWidget(new_btn)
        right.addLayout(header_row)
        right.addSpacing(14)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        right.addWidget(div)
        right.addSpacing(16)

        lbl_style = (
            f"QLabel {{ font-size: 11px; font-weight: 700; color: {T.TEXT_SEC}; "
            f"background: transparent; border: none; letter-spacing: 0.8px; }}"
        )

        # Project name
        pn_lbl = QLabel("PROJECT NAME")
        pn_lbl.setStyleSheet(lbl_style)
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("e.g. Riverside Cultural Center")
        self.project_name.setStyleSheet(T.input_field())
        self.project_name.setMinimumHeight(38)
        right.addWidget(pn_lbl)
        right.addSpacing(6)
        right.addWidget(self.project_name)
        right.addSpacing(14)

        # Client name
        cn_lbl = QLabel("CLIENT NAME")
        cn_lbl.setStyleSheet(lbl_style)
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("e.g. City of Portland")
        self.client_name.setStyleSheet(T.input_field())
        self.client_name.setMinimumHeight(38)
        right.addWidget(cn_lbl)
        right.addSpacing(6)
        right.addWidget(self.client_name)
        right.addSpacing(14)

        # Assign employees
        assign_lbl = QLabel("ASSIGN EMPLOYEES")
        assign_lbl.setStyleSheet(lbl_style)
        right.addWidget(assign_lbl)
        right.addSpacing(8)

        emp_scroll = QScrollArea()
        emp_scroll.setWidgetResizable(True)
        emp_scroll.setMinimumHeight(self.EMP_LIST_MIN_H)
        emp_scroll.setMaximumHeight(self.EMP_LIST_MAX_H)
        emp_scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; background: {T.SURFACE}; }}"
        )
        self.emp_scroll = emp_scroll  # kept for resizeEvent
        emp_container = QWidget()
        emp_container.setStyleSheet(f"QWidget {{ background: {T.SURFACE}; }}")
        self.employee_checkboxes = {}
        self.employee_roles      = {}
        self.employee_container  = QVBoxLayout(emp_container)
        self.employee_container.setContentsMargins(0, 0, 0, 0)
        self.employee_container.setSpacing(0)
        emp_scroll.setWidget(emp_container)
        right.addWidget(emp_scroll)
        right.addSpacing(18)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.save_btn = QPushButton("Create Project")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setMinimumWidth(120)
        self.save_btn.setStyleSheet(T.btn_primary())
        self.save_btn.clicked.connect(self.save_project)

        self.delete_btn = QPushButton("🗑  Delete Project")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.setStyleSheet(T.btn_danger())
        self.delete_btn.clicked.connect(self.delete_project)
        self.delete_btn.hide()

        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch()
        right.addLayout(btn_row)
        right.addStretch()

        self.project_name.returnPressed.connect(self.save_btn.click)
        self.client_name.returnPressed.connect(self.save_btn.click)

        body_layout.addWidget(left_panel)
        body_layout.addWidget(right_outer, 1)
        root_layout.addWidget(body, 1)

        self.load_projects()
        self.load_employees()

    def _go_back(self):
        mw = self.window()
        if hasattr(mw, "go_back"):
            mw.go_back()

    # ── Responsive layout ────────────────────────────────────────────────────
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._apply_responsive_sizing(event.size().width(), event.size().height())

    def _apply_responsive_sizing(self, width, height):
        # Sidebar scales with window width instead of staying at a fixed
        # 200-280px, clamped so it stays usable on very small/large screens.
        sidebar_w = max(self.SIDEBAR_MIN_W, min(self.SIDEBAR_MAX_W, int(width * self.SIDEBAR_RATIO)))
        self.left_panel.setMinimumWidth(sidebar_w)
        self.left_panel.setMaximumWidth(sidebar_w)

        # Employee list gets more/less vertical room depending on the
        # window height, instead of being stuck at 160-240px always.
        emp_h = max(self.EMP_LIST_MIN_H, min(self.EMP_LIST_MAX_H, int(height * self.EMP_LIST_RATIO)))
        self.emp_scroll.setMinimumHeight(emp_h)
        self.emp_scroll.setMaximumHeight(emp_h)

        # Scale a couple of key font sizes for very small / very large windows.
        scale = max(self.FONT_SCALE_MIN, min(self.FONT_SCALE_MAX, width / self.BASE_WINDOW_W))
        title_size = round(15 * scale)
        self.right_title.setStyleSheet(
            f"font-size: {title_size}px; font-weight: 700; color: {T.TEXT};"
        )

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_projects(self):
        self.project_list.clear()
        try:
            projects = self.fb.get_all_projects()
            for pid, project in projects.items():
                count = len(project.get("assigned_users", {}))
                item  = QListWidgetItem()
                item.setData(Qt.UserRole, pid)
                item.setData(Qt.UserRole + 1, {
                    "name":   project["name"],
                    "client": project["client_name"],
                    "count":  count,
                })
                self.project_list.addItem(item)

            # Custom delegate-style rendering via item widget
            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                d    = item.data(Qt.UserRole + 1)
                w    = self._make_project_item_widget(d["name"], d["client"], d["count"])
                # Force a minimum height so rows never overlap: sizeHint()
                # can come back too small before the widget's layout has
                # fully settled, which is what caused the overlapping text
                # you saw in the list.
                hint = w.sizeHint()
                item.setSizeHint(QSize(hint.width(), max(hint.height(), self.LIST_ITEM_MIN_H)))
                self.project_list.setItemWidget(item, w)

            self.project_count_lbl.setText(str(len(projects)))
            logger.info(f"Loaded {len(projects)} projects")
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load projects: {str(e)}")

    @staticmethod
    def _display(text: str) -> str:
        """Title-case a string that may be ALL CAPS for nicer display."""
        if text == text.upper() and len(text) > 2:
            return text.title()
        return text

    def _make_project_item_widget(self, name, client, count):
        w = QWidget()
        w.setStyleSheet("QWidget { background: transparent; border: none; }")
        w.setMinimumHeight(self.LIST_ITEM_MIN_H)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(20, 14, 20, 14)
        vl.setSpacing(3)

        name_lbl = QLabel(self._display(name))
        name_lbl.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; "
            f"background: transparent; border: none; letter-spacing: 0.1px; }}"
        )
        client_lbl = QLabel(self._display(client))
        client_lbl.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: {T.TEXT_SEC}; "
            f"background: transparent; border: none; }}"
        )
        assigned_lbl = QLabel(f"{count} assigned")
        assigned_lbl.setStyleSheet(
            f"QLabel {{ font-size: 10px; color: {T.TEXT_HINT}; "
            f"background: transparent; border: none; }}"
        )
        vl.addWidget(name_lbl)
        vl.addWidget(client_lbl)
        vl.addWidget(assigned_lbl)
        return w

    def load_employees(self):
        try:
            users_data = self.fb.root.child("users").get() or {}
            while self.employee_container.count():
                item = self.employee_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.employee_checkboxes.clear()
            self.employee_roles.clear()

            for uid, user in users_data.items():
                role = user.get("role", "")
                if role not in ["employee", "admin"]:
                    continue

                row = QFrame()
                row.setStyleSheet(
                    f"QFrame {{ background: {T.SURFACE}; border: none; "
                    f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
                )
                rl = QHBoxLayout(row)
                rl.setContentsMargins(16, 12, 16, 12)
                rl.setSpacing(14)

                cb = QCheckBox()
                cb.setStyleSheet(
                    f"QCheckBox {{ background: transparent; border: none; spacing: 0; }}"
                    f"QCheckBox::indicator {{ width: 18px; height: 18px; "
                    f"border: 1.5px solid {T.BORDER_SOLID}; border-radius: 4px; "
                    f"background: {T.SURFACE}; }}"
                    f"QCheckBox::indicator:checked {{ background: {T.ACCENT}; "
                    f"border-color: {T.ACCENT}; }}"
                )
                self.employee_checkboxes[uid] = cb

                # Name + email stacked
                info = QWidget()
                info.setStyleSheet("QWidget { background: transparent; border: none; }")
                il = QVBoxLayout(info)
                il.setContentsMargins(0, 0, 0, 0)
                il.setSpacing(1)
                name_lbl = QLabel(self._display(user.get("username", "")))
                name_lbl.setStyleSheet(
                    f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; "
                    f"background: transparent; border: none; }}"
                )
                email_lbl = QLabel(user.get("email", ""))
                email_lbl.setStyleSheet(
                    f"QLabel {{ font-size: 11px; color: {T.TEXT_SEC}; "
                    f"background: transparent; border: none; font-family: 'Courier New', monospace; }}"
                )
                il.addWidget(name_lbl)
                il.addWidget(email_lbl)

                # Role badge
                role_label = "Admin" if role == "admin" else "Employee"
                fg, bg = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
                badge = QLabel(role_label)
                badge.setStyleSheet(
                    f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
                    f"padding: 2px 10px; font-size: 11px; font-weight: 700; border: none; }}"
                )
                badge.setFixedHeight(22)

                rl.addWidget(cb)
                rl.addWidget(info, 1)
                rl.addWidget(badge)
                self.employee_container.addWidget(row)

            logger.info(f"Loaded {len(self.employee_checkboxes)} employees")
        except Exception as e:
            logger.error(f"Error loading employees: {str(e)}")

    def load_project_data(self, item):
        project_id = item.data(Qt.UserRole)
        self.selected_project_id = project_id
        try:
            project = self.fb.get_project(project_id)
            if not project:
                ModernMessageBox.warning(self, "Error", "Project not found")
                return

            self.project_name.setText(self._display(project.get("name", "")))
            self.client_name.setText(self._display(project.get("client_name", "")))
            self.right_title.setText("Edit Project")
            self.delete_btn.show()
            self.save_btn.setText("Save Changes")

            all_users      = self.fb.root.child("users").get() or {}
            valid_user_ids = set(all_users.keys())
            assigned_users = project.get("assigned_users", {})
            cleaned        = {uid: v for uid, v in assigned_users.items() if uid in valid_user_ids}

            if len(cleaned) != len(assigned_users):
                project["assigned_users"] = cleaned
                self.fb.save_project(project_id, project)

            for uid, cb in self.employee_checkboxes.items():
                cb.setChecked(uid in cleaned)

            logger.info(f"Loaded project: {project_id}")
        except Exception as e:
            logger.error(f"Error loading project data: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load project: {str(e)}")

    def create_new_project(self):
        self.selected_project_id = None
        self.project_name.clear()
        self.client_name.clear()
        for cb in self.employee_checkboxes.values():
            cb.setChecked(False)
        self.right_title.setText("New Project")
        self.delete_btn.hide()
        self.save_btn.setText("Create Project")

    def delete_project(self):
        if not self.selected_project_id:
            ModernMessageBox.warning(self, "No Selection", "Select a project to delete.")
            return
        try:
            project      = self.fb.get_project(self.selected_project_id)
            project_name = project.get("name", "Unknown")
            if ModernMessageBox.confirm_delete(self, project_name):
                self.fb.root.child("projects").child(self.selected_project_id).delete()
                self.fb.root.child("drawings").child(self.selected_project_id).delete()
                self.fb.root.child("notes").child(self.selected_project_id).delete()
                logger.info(f"Deleted project: {self.selected_project_id}")
                self.create_new_project()
                self.load_projects()
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to delete project: {str(e)}")

    def save_project(self):
        project_name = self.project_name.text().strip()
        client_name  = self.client_name.text().strip()
        if not project_name or not client_name:
            ModernMessageBox.warning(self, "Validation", "Project name and client are required.")
            return

        assigned_users = {uid: True for uid, cb in self.employee_checkboxes.items() if cb.isChecked()}

        try:
            if self.current_user:
                actor = User(
                    self.current_user["user_id"], self.current_user["username"],
                    self.current_user["email"],   self.current_user["role"]
                )
            else:
                actor = User("admin", "Admin", "admin@sot.com", "admin")

            if self.selected_project_id:
                project_data = {
                    "project_id":     self.selected_project_id,
                    "name":           project_name,
                    "client_name":    client_name,
                    "assigned_users": assigned_users,
                }
                self.fb.save_project(self.selected_project_id, project_data)
                logger.info(f"Updated project: {self.selected_project_id}")
                ModernMessageBox.success(self, "Saved", f'"{project_name}" has been updated.')
            else:
                project_id   = str(uuid.uuid4())
                project_data = self.project_manager.create_project(
                    actor, project_id, project_name, client_name
                )
                project_data["assigned_users"] = assigned_users
                self.fb.save_project(project_id, project_data)
                self.fb.create_project_drawings_from_template(project_id)
                logger.info(f"Created project: {project_id}")
                ModernMessageBox.success(self, "Created", f'"{project_name}" created with template drawings.')

            self.load_projects()
        except PermissionError as e:
            ModernMessageBox.error(self, "Permission Denied", str(e))
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to save project: {str(e)}")