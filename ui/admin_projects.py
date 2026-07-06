# Admin Projects - Now with Enter key support and fewer unnecessary dialogs
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QLineEdit, QCheckBox, QFrame
)
from PySide6.QtCore import Qt
from services.firebase_client import FirebaseClient
from core.projects import ProjectManager
from core.auth import User
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import uuid


class AdminProjects(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.fb = FirebaseClient()
        self.project_manager = ProjectManager(self.fb)
        self.selected_project_id = None

        self.setStyleSheet("""
            QWidget {
                background: #e8ebf0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
                color: #1e293b;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        # ===== LEFT: PROJECT LIST =====
        left_frame = QFrame()
        left_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        
        left = QVBoxLayout(left_frame)
        left.setContentsMargins(32, 32, 32, 32)
        left.setSpacing(16)
        
        left_title = QLabel("Existing Projects")
        left_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        left.addWidget(left_title)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 0;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 20px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 12px;
                background: #f8fafc;
                color: #1e293b;
            }
            QListWidget::item:hover {
                background: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            QListWidget::item:selected {
                background: white;
                border: 2px solid #1e40af;
                color: #1e293b;
            }
        """)
        self.project_list.itemClicked.connect(self.load_project_data)
        left.addWidget(self.project_list)

        # ===== RIGHT: EDIT / CREATE =====
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        
        right = QVBoxLayout(right_frame)
        right.setContentsMargins(32, 32, 32, 32)
        right.setSpacing(20)
        
        # Header with buttons
        header_layout = QHBoxLayout()
        self.right_title = QLabel("Edit Project")
        self.right_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        new_project_btn = QPushButton("New Project")
        new_project_btn.setCursor(Qt.PointingHandCursor)
        new_project_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                border: 1px solid #1e40af;
                color: #1e40af;
            }
        """)
        new_project_btn.clicked.connect(self.create_new_project)
        
        header_layout.addWidget(self.right_title)
        header_layout.addStretch()
        header_layout.addWidget(new_project_btn)
        right.addLayout(header_layout)

        # Project Name
        proj_label = QLabel("Project Name")
        proj_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Enter project name")
        self.project_name.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #1e293b;
            }
            QLineEdit:focus {
                background: #e2e8f0;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)

        # Client Name
        client_label = QLabel("Client Name")
        client_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("Enter client name")
        self.client_name.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #1e293b;
            }
            QLineEdit:focus {
                background: #e2e8f0;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)

        right.addWidget(proj_label)
        right.addWidget(self.project_name)
        right.addSpacing(8)
        right.addWidget(client_label)
        right.addWidget(self.client_name)

        # Assign Employees
        assign_label = QLabel("Assign Employees")
        assign_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        right.addWidget(assign_label)
        
        # Container for employee checkboxes
        self.employee_checkboxes = {}
        self.employee_container = QVBoxLayout()
        right.addLayout(self.employee_container)

        # FIX: Add button container with Save and Delete buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        # Delete button (only visible when editing)
        self.delete_btn = QPushButton("🗑️ Delete Project")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #dc2626;
                border: 2px solid #dc2626;
                border-radius: 8px;
                padding: 14px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background: #dc2626;
                color: white;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_project)
        self.delete_btn.hide()  # Hidden by default
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background: #1e3a8a;
            }
        """)
        self.save_btn.clicked.connect(self.save_project)

        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.save_btn, 1)  # Save button takes more space

        right.addStretch()
        right.addLayout(button_layout)

        # NEW: Connect Enter key to save button
        self.project_name.returnPressed.connect(self.save_btn.click)
        self.client_name.returnPressed.connect(self.save_btn.click)

        root.addWidget(left_frame, 1)
        root.addWidget(right_frame, 1)
        
        # Load initial data
        self.load_projects()
        self.load_employees()

    def load_projects(self):
        """Load all projects from Firebase"""
        self.project_list.clear()
        
        try:
            projects = self.fb.get_all_projects()
            
            for pid, project in projects.items():
                assigned_count = len(project.get("assigned_users", {}))
                item_text = f"{project['name']}\n{project['client_name']}\n{assigned_count} employee(s) assigned"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, pid)
                self.project_list.addItem(item)
            
            logger.info(f"Loaded {len(projects)} projects")
            
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load projects: {str(e)}")

    def load_employees(self):
        """
        Load all employees for assignment
        FIX: Now filters out deleted users from the assignment list
        """
        try:
            users_data = self.fb.root.child("users").get() or {}
            
            # Clear existing checkboxes
            while self.employee_container.count():
                item = self.employee_container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.employee_checkboxes.clear()
            
            # FIX: Get current list of valid user IDs  
            valid_user_ids = set(users_data.keys())
            
            # Create checkbox for each employee/admin (ONLY if they still exist)
            for uid, user in users_data.items():
                if user.get('role') in ['employee', 'admin']:
                    checkbox = QCheckBox(f"{user.get('username')} ({user.get('email')})")
                    checkbox.setStyleSheet("""
                        QCheckBox {
                            font-size: 14px;
                            color: #1e293b;
                            background: transparent;
                            spacing: 8px;
                        }
                        QCheckBox::indicator {
                            width: 20px;
                            height: 20px;
                            border-radius: 4px;
                        }
                        QCheckBox::indicator:unchecked {
                            background: white;
                            border: 2px solid #cbd5e1;
                        }
                        QCheckBox::indicator:checked {
                            background: #1e40af;
                            border: 2px solid #1e40af;
                        }
                    """)
                    self.employee_checkboxes[uid] = checkbox
                    self.employee_container.addWidget(checkbox)
            
            logger.info(f"Loaded {len(self.employee_checkboxes)} employees")
            
        except Exception as e:
            logger.error(f"Error loading employees: {str(e)}")


    def load_project_data(self, item):
        """
        Load selected project data into form
        FIX: Filters out deleted users from checked assignments
        """
        project_id = item.data(Qt.UserRole)
        self.selected_project_id = project_id
        
        try:
            project = self.fb.get_project(project_id)
            
            if not project:
                ModernMessageBox.warning(self, "Error", "Project not found")
                return
            
            # Populate form
            self.project_name.setText(project.get('name', ''))
            self.client_name.setText(project.get('client_name', ''))
            
            # Update header
            self.right_title.setText("Edit Project")
            
            # Show delete button when editing
            self.delete_btn.show()
            self.save_btn.setText("Save Changes")
            
            # FIX: Get current valid users
            all_users = self.fb.root.child("users").get() or {}
            valid_user_ids = set(all_users.keys())
            
            # Check assigned employees (ONLY if they still exist)
            assigned_users = project.get('assigned_users', {})
            
            # FIX: Auto-clean deleted users from project assignments
            cleaned_assignments = {uid: val for uid, val in assigned_users.items() if uid in valid_user_ids}
            if len(cleaned_assignments) != len(assigned_users):
                # Some users were deleted - update project
                logger.info(f"Cleaning {len(assigned_users) - len(cleaned_assignments)} deleted users from project {project_id}")
                project['assigned_users'] = cleaned_assignments
                self.fb.save_project(project_id, project)
            
            # Update checkboxes
            for uid, checkbox in self.employee_checkboxes.items():
                checkbox.setChecked(uid in cleaned_assignments)
            
            logger.info(f"Loaded project data for: {project_id}")
            
        except Exception as e:
            logger.error(f"Error loading project data: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load project: {str(e)}")

    def create_new_project(self):
        """Clear form for creating a new project"""
        self.selected_project_id = None
        self.project_name.clear()
        self.client_name.clear()
        
        # Uncheck all employees
        for checkbox in self.employee_checkboxes.values():
            checkbox.setChecked(False)
        
        self.right_title.setText("Create New Project")
        self.delete_btn.hide()  # Hide delete button for new projects
        self.save_btn.setText("Create Project")
        
        logger.info("Creating new project")

    def delete_project(self):
        """Delete the currently selected project - ONLY DIALOG KEPT"""
        if not self.selected_project_id:
            ModernMessageBox.warning(self, "No Project Selected", "Please select a project to delete")
            return
        
        # Get project details for confirmation
        try:
            project = self.fb.get_project(self.selected_project_id)
            project_name = project.get('name', 'Unknown')
            
            # Confirmation dialog using modern dialog
            if ModernMessageBox.confirm_delete(self, project_name):
                # Delete project and all related data
                self.fb.root.child("projects").child(self.selected_project_id).delete()
                self.fb.root.child("drawings").child(self.selected_project_id).delete()
                self.fb.root.child("notes").child(self.selected_project_id).delete()
                
                logger.info(f"Deleted project: {self.selected_project_id}")
                
                # Clear form and reload projects (NO SUCCESS DIALOG)
                self.create_new_project()
                self.load_projects()
                
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to delete project: {str(e)}")

    def save_project(self):
        """Save or update project - NO SUCCESS DIALOG"""
        project_name = self.project_name.text().strip()
        client_name = self.client_name.text().strip()
        
        # Validation
        if not project_name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a project name")
            return
        
        if not client_name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a client name")
            return
        
        # Get assigned users
        assigned_users = {}
        for uid, checkbox in self.employee_checkboxes.items():
            if checkbox.isChecked():
                assigned_users[uid] = True
        
        try:
            # Create actor user
            if self.current_user:
                actor = User(
                    user_id=self.current_user['user_id'],
                    username=self.current_user['username'],
                    email=self.current_user['email'],
                    role=self.current_user['role']
                )
            else:
                # Fallback for testing
                actor = User("admin", "Admin", "admin@sot.com", "admin")
            
            if self.selected_project_id:
                # Update existing project
                project_data = {
                    "project_id": self.selected_project_id,
                    "name": project_name,
                    "client_name": client_name,
                    "assigned_users": assigned_users
                }
                self.fb.save_project(self.selected_project_id, project_data)
                
                logger.info(f"Updated project: {self.selected_project_id}")
                
                # NO SUCCESS DIALOG - just reload
            else:
                # Create new project
                project_id = str(uuid.uuid4())
                
                project_data = self.project_manager.create_project(
                    actor=actor,
                    project_id=project_id,
                    name=project_name,
                    client_name=client_name
                )
                
                # Update assigned users
                project_data["assigned_users"] = assigned_users
                self.fb.save_project(project_id, project_data)
                
                # Create drawings from template
                self.fb.create_project_drawings_from_template(project_id)
                
                logger.info(f"Created project: {project_id}")
                
                # NO SUCCESS DIALOG - just reload
            
            # Reload projects list
            self.load_projects()
            
        except PermissionError as e:
            logger.error(f"Permission denied: {str(e)}")
            ModernMessageBox.error(self, "Permission Denied", str(e))
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to save project: {str(e)}")