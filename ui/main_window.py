from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QApplication, QStackedWidget
)
import sys
import utils.theme as T

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

        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        self.setMinimumSize(1024, 768)
        self.showMaximized()

        self.user = None
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"QStackedWidget {{ background: {T.BG}; }}")

        self.login_view = LoginView()
        self.login_view.login_success.connect(self.on_login_success)
        self.stack.addWidget(self.login_view)

        self.admin_dashboard    = None
        self.employee_dashboard = None
        self.projects_page  = None
        self.review_page    = None
        self.template_page  = None
        self.users_page     = None

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)

        self.setCentralWidget(root)
        self.stack.setCurrentWidget(self.login_view)

    # ── Navigation ─────────────────────────────────────────────────────────────
    def on_login_success(self, user):
        self.user = user
        if user.get("role") in ["admin", "super_admin"]:
            self.admin_dashboard = AdminDashboard(user, self.handle_logout)
            self.stack.addWidget(self.admin_dashboard)
            self.show_admin_dashboard()
        else:
            self.employee_dashboard = EmployeeDashboard(user, self.handle_logout)
            self.stack.addWidget(self.employee_dashboard)
            self.show_employee_dashboard()

    def show_admin_dashboard(self):
        if self.admin_dashboard:
            self.stack.setCurrentWidget(self.admin_dashboard)

    def show_employee_dashboard(self):
        if self.employee_dashboard:
            self.stack.setCurrentWidget(self.employee_dashboard)

    def show_projects(self):
        if self.projects_page is None:
            self.projects_page = AdminProjects(current_user=self.user)
            self.stack.addWidget(self.projects_page)
        else:
            self.projects_page.load_employees()
        self.stack.setCurrentWidget(self.projects_page)

    def show_review(self):
        if self.review_page is None:
            self.review_page = AdminReview()
            self.stack.addWidget(self.review_page)
        self.stack.setCurrentWidget(self.review_page)

    def show_templates(self):
        if self.template_page is None:
            self.template_page = AdminTemplate(
                user=self.user,
                on_back=self.go_back,
                on_logout=self.handle_logout,
            )
            self.stack.addWidget(self.template_page)
        self.stack.setCurrentWidget(self.template_page)

    def show_users(self):
        if self.users_page is None:
            self.users_page = SuperAdminUsers(current_user=self.user)
            self.stack.addWidget(self.users_page)
        else:
            self.users_page.load_users()
        self.stack.setCurrentWidget(self.users_page)

    def show_drawing_detail(self, project_id, drawing_id):
        from ui.drawing_detail import DrawingDetail
        detail_widget = DrawingDetail(project_id, drawing_id, current_user=self.user)
        self.stack.addWidget(detail_widget)
        self.stack.setCurrentWidget(detail_widget)

    def go_back(self):
        if self.user and self.user.get("role") in ["admin", "super_admin"]:
            self.show_admin_dashboard()
        elif self.user:
            self.show_employee_dashboard()

    def handle_logout(self):
        self.user = None
        self.admin_dashboard    = None
        self.employee_dashboard = None
        self.projects_page  = None
        self.review_page    = None
        self.template_page  = None
        self.users_page     = None
        self.stack.setCurrentWidget(self.login_view)
        self.login_view.email_input.clear()
        self.login_view.password_input.clear()
        self.login_view.error_label.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
