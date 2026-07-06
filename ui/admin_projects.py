# Admin Projects
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QCheckBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from services.firebase_client import FirebaseClient
from core.projects import ProjectManager
from core.auth import User
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import utils.theme as T
import uuid


class AdminProjects(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user       = current_user
        self.fb                 = FirebaseClient()
        self.project_manager    = ProjectManager(self.fb)
        self.selected_project_id = None

        self.setStyleSheet(T.app_base())

        root = QHBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── LEFT: project list ────────────────────────────────────────────────
        left_card = QFrame()
        left_card.setStyleSheet(T.card())
        left = QVBoxLayout(left_card)
        left.setContentsMargins(24, 24, 24, 24)
        left.setSpacing(14)

        left_header = QHBoxLayout()
        left_title = QLabel("Projects")
        left_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")
        self.project_count_lbl = QLabel("0")
        self.project_count_lbl.setStyleSheet(f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600;")
        left_header.addWidget(left_title)
        left_header.addStretch()
        left_header.addWidget(self.project_count_lbl)
        left.addLayout(left_header)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(T.list_widget())
        self.project_list.itemClicked.connect(self.load_project_data)
        left.addWidget(self.project_list)

        # ── RIGHT: create / edit form ─────────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(T.card())

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        right_scroll.setWidget(right_card)

        right = QVBoxLayout(right_card)
        right.setContentsMargins(28, 28, 28, 28)
        right.setSpacing(0)

        # Header row
        header_row = QHBoxLayout()
        self.right_title = QLabel("New Project")
        self.right_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")

        new_btn = QPushButton("+ New Project")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setFixedHeight(32)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.ACCENT_BG}; color: {T.ACCENT};
                border: 1px solid {T.ACCENT}40; border-radius: 5px;
                font-size: 12px; font-weight: 600; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {T.ACCENT}18; }}
        """)
        new_btn.clicked.connect(self.create_new_project)
        header_row.addWidget(self.right_title)
        header_row.addStretch()
        header_row.addWidget(new_btn)
        right.addLayout(header_row)
        right.addSpacing(24)

        # Project name
        pn_lbl = QLabel("Project Name")
        pn_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; background: transparent;")
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("e.g. Office Renovation 2024")
        self.project_name.setStyleSheet(T.input_field_flat())
        self.project_name.setMinimumHeight(40)
        right.addWidget(pn_lbl)
        right.addSpacing(6)
        right.addWidget(self.project_name)
        right.addSpacing(16)

        # Client name
        cn_lbl = QLabel("Client Name")
        cn_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; background: transparent;")
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("e.g. Acme Corporation")
        self.client_name.setStyleSheet(T.input_field_flat())
        self.client_name.setMinimumHeight(40)
        right.addWidget(cn_lbl)
        right.addSpacing(6)
        right.addWidget(self.client_name)
        right.addSpacing(20)

        # Assign employees section
        assign_lbl = QLabel("Assign Employees")
        assign_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; background: transparent;")
        right.addWidget(assign_lbl)
        right.addSpacing(10)

        # Employee checkboxes container (scrollable)
        emp_scroll = QScrollArea()
        emp_scroll.setWidgetResizable(True)
        emp_scroll.setMaximumHeight(200)
        emp_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1.5px solid {T.BORDER};
                border-radius: {T.RADIUS_SM};
                background: {T.BG};
            }}
        """)
        emp_container = QWidget()
        emp_container.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        self.employee_checkboxes = {}
        self.employee_container  = QVBoxLayout(emp_container)
        self.employee_container.setContentsMargins(14, 12, 14, 12)
        self.employee_container.setSpacing(8)
        emp_scroll.setWidget(emp_container)
        right.addWidget(emp_scroll)
        right.addSpacing(24)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.delete_btn = QPushButton("Delete Project")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.setStyleSheet(T.btn_danger())
        self.delete_btn.clicked.connect(self.delete_project)
        self.delete_btn.hide()

        self.save_btn = QPushButton("Create Project")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet(T.btn_primary())
        self.save_btn.clicked.connect(self.save_project)

        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        right.addLayout(btn_row)
        right.addStretch()

        self.project_name.returnPressed.connect(self.save_btn.click)
        self.client_name.returnPressed.connect(self.save_btn.click)

        root.addWidget(left_card, 1)
        root.addWidget(right_scroll, 1)

        self.load_projects()
        self.load_employees()

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_projects(self):
        self.project_list.clear()
        try:
            projects = self.fb.get_all_projects()
            for pid, project in projects.items():
                count = len(project.get("assigned_users", {}))
                item  = QListWidgetItem(f"{project['name']}\n{project['client_name']}  ·  {count} employee{'s' if count != 1 else ''}")
                item.setData(Qt.UserRole, pid)
                self.project_list.addItem(item)
            self.project_count_lbl.setText(str(len(projects)))
            logger.info(f"Loaded {len(projects)} projects")
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load projects: {str(e)}")

    def load_employees(self):
        try:
            users_data = self.fb.root.child("users").get() or {}
            while self.employee_container.count():
                item = self.employee_container.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            self.employee_checkboxes.clear()

            for uid, user in users_data.items():
                if user.get("role") in ["employee", "admin"]:
                    cb = QCheckBox(f"{user.get('username')}  ({user.get('email')})")
                    cb.setStyleSheet(f"""
                        QCheckBox {{ font-size: 13px; color: {T.TEXT}; background: transparent; spacing: 8px; }}
                        QCheckBox::indicator {{ width: 17px; height: 17px; border: 1.5px solid {T.BORDER_MED}; border-radius: 4px; background: {T.SURFACE}; }}
                        QCheckBox::indicator:checked {{ background: {T.ACCENT}; border-color: {T.ACCENT}; }}
                    """)
                    self.employee_checkboxes[uid] = cb
                    self.employee_container.addWidget(cb)

            logger.info(f"Loaded {len(self.employee_checkboxes)} employees")
        except Exception as e:
            logger.error(f"Error loading employees: {str(e)}")

    def load_project_data(self, item):
        project_id = item.data(Qt.UserRole)
        self.selected_project_id = project_id
        try:
            project = self.fb.get_project(project_id)
            if not project:
                ModernMessageBox.warning(self, "Error", "Project not found"); return

            self.project_name.setText(project.get("name", ""))
            self.client_name.setText(project.get("client_name", ""))
            self.right_title.setText("Edit Project")
            self.delete_btn.show()
            self.save_btn.setText("Save Changes")

            all_users       = self.fb.root.child("users").get() or {}
            valid_user_ids  = set(all_users.keys())
            assigned_users  = project.get("assigned_users", {})
            cleaned         = {uid: v for uid, v in assigned_users.items() if uid in valid_user_ids}

            if len(cleaned) != len(assigned_users):
                project["assigned_users"] = cleaned
                self.fb.save_project(project_id, project)

            for uid, cb in self.employee_checkboxes.items():
                cb.setChecked(uid in cleaned)

            logger.info(f"Loaded project data: {project_id}")
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
            ModernMessageBox.warning(self, "No Selection", "Select a project to delete"); return
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
        if not project_name:
            ModernMessageBox.warning(self, "Required", "Please enter a project name"); return
        if not client_name:
            ModernMessageBox.warning(self, "Required", "Please enter a client name"); return

        assigned_users = {uid: True for uid, cb in self.employee_checkboxes.items() if cb.isChecked()}

        try:
            if self.current_user:
                actor = User(self.current_user["user_id"], self.current_user["username"],
                             self.current_user["email"], self.current_user["role"])
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
            else:
                project_id   = str(uuid.uuid4())
                project_data = self.project_manager.create_project(actor, project_id, project_name, client_name)
                project_data["assigned_users"] = assigned_users
                self.fb.save_project(project_id, project_data)
                self.fb.create_project_drawings_from_template(project_id)
                logger.info(f"Created project: {project_id}")

            self.load_projects()
        except PermissionError as e:
            ModernMessageBox.error(self, "Permission Denied", str(e))
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to save project: {str(e)}")
