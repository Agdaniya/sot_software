from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QApplication, QFrame
)
from PySide6.QtCore import Qt
import sys

from ui.login_view import LoginView
from ui.admin_dashboard import AdminDashboard
from ui.employee_dashboard import EmployeeDashboard
from ui.admin_projects import AdminProjects
from ui.admin_review import AdminReview
from ui.admin_template import AdminTemplate
from ui.superadmin_users import SuperAdminUsers


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOT – Staff Operations Tracker")
        
        # FIX: Get screen geometry and set window to fill entire screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        
        # Set minimum size to ensure it stays large
        self.setMinimumSize(1024, 768)
        
        # Start maximized to fill the screen
        self.showMaximized()
        
        self.user = None
        self.stack = QStackedWidget()

        # Create login view first
        self.login_view = LoginView()
        self.login_view.login_success.connect(self.on_login_success)
        self.stack.addWidget(self.login_view)
        
        # Initialize dashboard variables
        self.admin_dashboard = None
        self.employee_dashboard = None
        
        # Initialize other pages as None (will be created when needed)
        self.projects_page = None
        self.review_page = None
        self.template_page = None
        self.users_page = None

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(80)
        self.header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border: none;
            }
        """)
        
        h = QHBoxLayout(self.header)
        h.setContentsMargins(40, 0, 40, 0)
        
        # Back button
        self.back_btn = QPushButton("←")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedSize(40, 40)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.hide()
        
        # Title
        self.header_title = QLabel("Dashboard")
        self.header_title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }
        """)
        
        h.addWidget(self.back_btn)
        h.addSpacing(12)
        h.addWidget(self.header_title)
        h.addStretch()
        
        # Hide header initially for login view
        self.header.hide()

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.stack)

        self.setCentralWidget(root)

        # Start with login view
        self.stack.setCurrentWidget(self.login_view)

    # -------- Navigation API --------
    def on_login_success(self, user):
        """Called when user successfully logs in"""
        self.user = user
        
        # Create appropriate dashboard based on role
        if user.get("role") in ["admin", "super_admin"]:
            self.admin_dashboard = AdminDashboard(user, self.handle_logout)
            self.stack.addWidget(self.admin_dashboard)
            self.show_admin_dashboard()
        else:
            self.employee_dashboard = EmployeeDashboard(user, self.handle_logout)
            self.stack.addWidget(self.employee_dashboard)
            self.show_employee_dashboard()
        
        # Show header after login
        self.header.show()
    
    def show_admin_dashboard(self):
        if hasattr(self, 'admin_dashboard') and self.admin_dashboard:
            self.header_title.setText("Admin Dashboard")
            self.back_btn.hide()
            self.header.hide()  # Dashboard has its own header
            self.stack.setCurrentWidget(self.admin_dashboard)

    def show_employee_dashboard(self):
        if hasattr(self, 'employee_dashboard') and self.employee_dashboard:
            self.header_title.setText("Employee Dashboard")
            self.back_btn.hide()
            self.header.hide()  # Dashboard has its own header
            self.stack.setCurrentWidget(self.employee_dashboard)

    def show_projects(self):
        # Create projects page if it doesn't exist
        if self.projects_page is None:
            self.projects_page = AdminProjects(current_user=self.user)
            self.stack.addWidget(self.projects_page)
        else:
            # FIX: Reload employees list when returning to this page
            # This ensures newly created employees show up immediately
            self.projects_page.load_employees()
        
        self.header.show()
        self.header_title.setText("Project Management")
        self.back_btn.show()
        self.stack.setCurrentWidget(self.projects_page)

    def show_review(self):
        # Create review page if it doesn't exist
        if self.review_page is None:
            self.review_page = AdminReview()
            self.stack.addWidget(self.review_page)
        
        self.header.show()
        self.header_title.setText("Review Submitted Drawings")
        self.back_btn.show()
        self.stack.setCurrentWidget(self.review_page)

    def show_templates(self):
        # Create template page if it doesn't exist
        if self.template_page is None:
            self.template_page = AdminTemplate()
            self.stack.addWidget(self.template_page)
        
        self.header.show()
        self.header_title.setText("Project Template Manager")
        self.back_btn.show()
        self.stack.setCurrentWidget(self.template_page)

    def show_users(self):
        # Create users page with current user if it doesn't exist
        if self.users_page is None:
            self.users_page = SuperAdminUsers(current_user=self.user)
            self.stack.addWidget(self.users_page)
        else:
            # FIX: Reload users list when returning to this page
            # This ensures any changes are reflected immediately
            self.users_page.load_users()
        
        self.header.show()
        self.header_title.setText("User Management")
        self.back_btn.show()
        self.stack.setCurrentWidget(self.users_page)

    def show_drawing_detail(self, project_id, drawing_id):
        """FIX: Pass current_user to DrawingDetail for notes and payment features"""
        from ui.drawing_detail import DrawingDetail
        
        # Create new drawing detail widget with current user
        detail_widget = DrawingDetail(project_id, drawing_id, current_user=self.user)
        
        # Add to stack
        self.stack.addWidget(detail_widget)
        
        # Switch to it
        self.header.hide()  # Drawing detail has its own header
        self.stack.setCurrentWidget(detail_widget)

    def go_back(self):
        if self.user and self.user.get("role") in ["admin", "super_admin"]:
            self.show_admin_dashboard()
        elif self.user:
            self.show_employee_dashboard()
    
    def handle_logout(self):
        """Handle logout - return to login view"""
        self.user = None
        self.header.hide()
        
        # Reset all pages
        self.admin_dashboard = None
        self.employee_dashboard = None
        self.projects_page = None
        self.review_page = None
        self.template_page = None
        self.users_page = None
        
        self.stack.setCurrentWidget(self.login_view)
        
        # Clear login form
        self.login_view.email_input.clear()
        self.login_view.password_input.clear()
        self.login_view.error_label.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())