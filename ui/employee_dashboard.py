from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QHBoxLayout, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from services.firebase_client import FirebaseClient
from utils.logger import logger


class EmployeeDashboard(QWidget):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.fb = FirebaseClient()
        self.current_project_id = None  # Track currently selected project

        self.setStyleSheet("""
            QWidget {
                background: #e8ebf0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
                color: #1e293b;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ================= HEADER =================
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Employee Dashboard")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }
        """)

        # FIX: Improved greeting with username
        greeting = self.get_greeting()
        subtitle = QLabel(f"{greeting}, {user['username']}! 👋")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 15px;
                background: transparent;
            }
        """)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)
        logout_btn.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_btn)

        main_layout.addWidget(header)

        # ================= CONTENT AREA =================
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(28)

        # ================= LEFT: PROJECTS =================
        left_frame = QFrame()
        left_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)

        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(28, 28, 28, 28)
        left_layout.setSpacing(14)

        projects_label = QLabel("Assigned Projects")
        projects_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)
        left_layout.addWidget(projects_label)

        # Search box for projects
        self.project_search = QLineEdit()
        self.project_search.setPlaceholderText("🔍 Search projects...")
        self.project_search.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
                background: #f1f5f9;
                font-size: 13px;
            }
            QLineEdit:focus {
                background: #e2e8f0;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        self.project_search.textChanged.connect(self.filter_projects)
        left_layout.addWidget(self.project_search)

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
                padding: 16px 18px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 10px;
                background: #f8fafc;
                color: #1e293b;
                font-size: 14px;
                line-height: 1.5;
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
        self.project_list.itemClicked.connect(self.load_drawings)
        left_layout.addWidget(self.project_list)

        # ================= RIGHT: DRAWINGS =================
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(28, 28, 28, 28)
        right_layout.setSpacing(14)

        drawings_label = QLabel("Project Drawings")
        drawings_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)
        right_layout.addWidget(drawings_label)

        self.drawing_list = QListWidget()
        self.drawing_list.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 0;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 16px 18px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 10px;
                background: #f8fafc;
                color: #1e293b;
                font-size: 14px;
                line-height: 1.5;
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
        self.drawing_list.itemClicked.connect(self.open_drawing)
        right_layout.addWidget(self.drawing_list)

        # Empty state
        self.empty_state = QLabel("Select a project to view drawings")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 13px;
                background: transparent;
                border: none;
                padding: 30px;
            }
        """)
        right_layout.addWidget(self.empty_state)
        self.drawing_list.hide()

        content_layout.addWidget(left_frame, 1)
        content_layout.addWidget(right_frame, 1)

        main_layout.addWidget(content)

        # ================= AUTO-REFRESH TIMER =================
        # CRITICAL: Auto-refresh every 3 seconds to show real-time updates
        # This prevents multiple employees from working on the same drawing
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(3000)  # Refresh every 3 seconds

        self.load_projects()

    def get_greeting(self):
        """Get time-appropriate greeting"""
        from datetime import datetime
        hour = datetime.now().hour
        
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def auto_refresh(self):
        """Auto-refresh to keep drawing statuses in sync across all users"""
        try:
            # If a project is selected, refresh its drawings
            if self.current_project_id:
                # Silently reload drawings without clearing selection
                current_item = self.drawing_list.currentItem()
                current_drawing_id = current_item.data(Qt.UserRole) if current_item else None
                
                # Reload the drawings list
                self.refresh_drawings_list()
                
                # Try to restore selection if drawing still exists
                if current_drawing_id:
                    for i in range(self.drawing_list.count()):
                        item = self.drawing_list.item(i)
                        if item.data(Qt.UserRole) == current_drawing_id:
                            self.drawing_list.setCurrentItem(item)
                            break
        except Exception as e:
            # Silently fail - don't disrupt user experience
            logger.error(f"Auto-refresh error: {str(e)}")

    def refresh_drawings_list(self):
        """Refresh the drawings list without losing current view"""
        if not self.current_project_id:
            return
        
        try:
            drawings = (
                self.fb.root
                .child("drawings")
                .child(self.current_project_id)
                .get() or {}
            )

            # Store current scroll position
            scroll_pos = self.drawing_list.verticalScrollBar().value()
            
            # Clear and rebuild list
            self.drawing_list.clear()

            for did, drawing in drawings.items():
                status = drawing['status'].replace('_', ' ').title()
                
                # Status badge text
                if drawing['status'] == 'completed':
                    badge = "Ready For Review"
                elif drawing['status'] == 'in_progress':
                    badge = "In Progress"
                elif drawing['status'] == 'submitted':
                    badge = "Submitted"
                elif drawing['status'] == 'admin_approved':
                    badge = "Admin Approved"
                elif drawing['status'] == 'admin_rejected':
                    badge = "Rejected - Needs Revision"
                elif drawing['status'] == 'client_approved':
                    badge = "Client Approved"
                else:
                    badge = "Not Started"
                
                # Count completed substeps
                substeps = drawing.get('sub_steps', {})
                completed = sum(1 for s in substeps.values() if s.get('completed', False))
                total = len(substeps)
                
                # Payment status
                payment_text = " [PAID]" if drawing.get('payment_received', False) else ""
                
                # Create list item
                d_item = QListWidgetItem()
                d_item.setText(f"{drawing['name']}\n{completed}/{total} steps • {badge}{payment_text}")
                d_item.setData(Qt.UserRole, did)
                self.drawing_list.addItem(d_item)
            
            # Restore scroll position
            self.drawing_list.verticalScrollBar().setValue(scroll_pos)
            
        except Exception as e:
            logger.error(f"Error refreshing drawings: {str(e)}")

    def load_projects(self):
        """Load projects assigned to this employee"""
        self.project_list.clear()
        
        try:
            projects = self.fb.root.child("projects").get() or {}

            for pid, project in projects.items():
                # Check if user_id is in assigned_users dict
                if self.user["user_id"] in project.get("assigned_users", {}):
                    item = QListWidgetItem(
                        f"{project['name']}\n{project['client_name']}"
                    )
                    item.setData(Qt.UserRole, pid)
                    self.project_list.addItem(item)
            
            logger.info(f"Loaded {self.project_list.count()} projects for user {self.user['user_id']}")
            
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")

    def filter_projects(self, text):
        """Filter projects based on search text"""
        text_lower = text.lower()
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def load_drawings(self, item):
        """Load drawings for selected project"""
        self.drawing_list.clear()
        self.empty_state.hide()
        self.drawing_list.show()
        
        project_id = item.data(Qt.UserRole)
        self.current_project_id = project_id  # Store for auto-refresh

        try:
            drawings = (
                self.fb.root
                .child("drawings")
                .child(project_id)
                .get() or {}
            )

            for did, drawing in drawings.items():
                status = drawing['status'].replace('_', ' ').title()
                
                # Status badge text
                if drawing['status'] == 'completed':
                    badge = "Ready For Review"
                elif drawing['status'] == 'in_progress':
                    badge = "In Progress"
                elif drawing['status'] == 'submitted':
                    badge = "Submitted"
                elif drawing['status'] == 'admin_approved':
                    badge = "Admin Approved"
                elif drawing['status'] == 'admin_rejected':
                    badge = "Rejected - Needs Revision"
                elif drawing['status'] == 'client_approved':
                    badge = "Client Approved"
                else:
                    badge = "Not Started"
                
                # Count completed substeps
                substeps = drawing.get('sub_steps', {})
                completed = sum(1 for s in substeps.values() if s.get('completed', False))
                total = len(substeps)
                
                # Payment status
                payment_text = " [PAID]" if drawing.get('payment_received', False) else ""
                
                # Create list item
                d_item = QListWidgetItem()
                d_item.setText(f"{drawing['name']}\n{completed}/{total} steps • {badge}{payment_text}")
                d_item.setData(Qt.UserRole, did)
                self.drawing_list.addItem(d_item)
            
            logger.info(f"Loaded {len(drawings)} drawings for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error loading drawings: {str(e)}")

    def open_drawing(self, item):
        """Open drawing detail view"""
        drawing_id = item.data(Qt.UserRole)
        project_item = self.project_list.currentItem()
        if not project_item:
            return
            
        project_id = project_item.data(Qt.UserRole)

        # Navigate via main window
        main_window = self.window()
        if hasattr(main_window, 'show_drawing_detail'):
            main_window.show_drawing_detail(project_id, drawing_id)

    def handle_logout(self):
        """Handle user logout"""
        try:
            # Stop the refresh timer
            self.refresh_timer.stop()
            
            self.fb.record_logout_time(self.user["user_id"])
            logger.info(f"User {self.user['user_id']} logged out")
        except Exception as e:
            logger.error(f"Error recording logout: {str(e)}")
        
        self.on_logout()