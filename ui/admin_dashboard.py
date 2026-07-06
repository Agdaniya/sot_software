from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QGridLayout, QMessageBox,
    QStackedWidget, QScrollArea, QDialog, QDateEdit, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon

from services.firebase_client import FirebaseClient

from ui.admin_projects import AdminProjects
from ui.admin_review import AdminReview
from ui.admin_template import AdminTemplate
from ui.superadmin_users import SuperAdminUsers


# Modern Date range dialog for employee reports
class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date Range")
        self.setModal(True)
        self.setMinimumWidth(480)
        
        # Modern styling
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QLabel {
                color: #1e293b;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title with icon
        title_layout = QHBoxLayout()
        icon = QLabel("📊")
        icon.setStyleSheet("QLabel { font-size: 24px; }")
        
        title = QLabel("Generate Employee Performance Report")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
            }
        """)
        
        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Description
        desc = QLabel("Select a date range for the report, or use all available data.")
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #64748b;
                line-height: 1.5;
            }
        """)
        layout.addWidget(desc)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("QFrame { background: #e2e8f0; max-height: 1px; }")
        layout.addWidget(divider)
        
        # All time checkbox (moved to top for better UX)
        self.all_time_checkbox = QCheckBox("📅 Use all time data (ignore date range)")
        self.all_time_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #cbd5e1;
            }
            QCheckBox::indicator:checked {
                background: #1e40af;
                border: 2px solid #1e40af;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMSAxTDQuNSA4TDEgNC41IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
        """)
        self.all_time_checkbox.toggled.connect(self.toggle_date_inputs)
        layout.addWidget(self.all_time_checkbox)
        
        # Date range container
        self.date_container = QFrame()
        date_layout = QVBoxLayout(self.date_container)
        date_layout.setSpacing(16)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start date
        start_frame = QFrame()
        start_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        start_layout = QVBoxLayout(start_frame)
        start_layout.setSpacing(8)
        start_layout.setContentsMargins(0, 0, 0, 0)
        
        start_label = QLabel("📅 Start Date")
        start_label.setStyleSheet("""
            QLabel { 
                font-size: 13px; 
                font-weight: 600; 
                color: #475569;
            }
        """)
        start_layout.addWidget(start_label)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setDisplayFormat("MMMM dd, yyyy")
        self.start_date.setStyleSheet("""
            QDateEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                color: #1e293b;
            }
            QDateEdit:focus {
                background: #f1f5f9;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 8px;
            }
            QCalendarWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                color: #1e293b;
                background: transparent;
                padding: 4px;
            }
            QCalendarWidget QMenu {
                background: white;
                border: 1px solid #e2e8f0;
            }
            QCalendarWidget QSpinBox {
                background: white;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
            QCalendarWidget QTableView {
                selection-background-color: #1e40af;
                selection-color: white;
            }
        """)
        start_layout.addWidget(self.start_date)
        date_layout.addWidget(start_frame)
        
        # End date
        end_frame = QFrame()
        end_frame.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        end_layout = QVBoxLayout(end_frame)
        end_layout.setSpacing(8)
        end_layout.setContentsMargins(0, 0, 0, 0)
        
        end_label = QLabel("📅 End Date")
        end_label.setStyleSheet("""
            QLabel { 
                font-size: 13px; 
                font-weight: 600; 
                color: #475569;
            }
        """)
        end_layout.addWidget(end_label)
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("MMMM dd, yyyy")
        self.end_date.setStyleSheet("""
            QDateEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                color: #1e293b;
            }
            QDateEdit:focus {
                background: #f1f5f9;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                margin-right: 8px;
            }
            QCalendarWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                color: #1e293b;
                background: transparent;
                padding: 4px;
            }
            QCalendarWidget QMenu {
                background: white;
                border: 1px solid #e2e8f0;
            }
            QCalendarWidget QSpinBox {
                background: white;
                border: 1px solid #e2e8f0;
                padding: 4px;
            }
            QCalendarWidget QTableView {
                selection-background-color: #1e40af;
                selection-color: white;
            }
        """)
        end_layout.addWidget(self.end_date)
        date_layout.addWidget(end_frame)
        
        layout.addWidget(self.date_container)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        
        quick_label = QLabel("Quick select:")
        quick_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #64748b;
                font-weight: 500;
            }
        """)
        quick_layout.addWidget(quick_label)
        
        last_7_btn = QPushButton("Last 7 days")
        last_7_btn.setCursor(Qt.PointingHandCursor)
        last_7_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: #475569;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        last_7_btn.clicked.connect(lambda: self.set_quick_range(7))
        
        last_30_btn = QPushButton("Last 30 days")
        last_30_btn.setCursor(Qt.PointingHandCursor)
        last_30_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: #475569;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        last_30_btn.clicked.connect(lambda: self.set_quick_range(30))
        
        this_month_btn = QPushButton("This month")
        this_month_btn.setCursor(Qt.PointingHandCursor)
        this_month_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                color: #475569;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        this_month_btn.clicked.connect(self.set_this_month)
        
        quick_layout.addWidget(last_7_btn)
        quick_layout.addWidget(last_30_btn)
        quick_layout.addWidget(this_month_btn)
        quick_layout.addStretch()
        
        layout.addLayout(quick_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #1e293b;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.setCursor(Qt.PointingHandCursor)
        generate_btn.setStyleSheet("""
            QPushButton {
                background: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1e3a8a;
            }
        """)
        generate_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(generate_btn)
        
        layout.addLayout(button_layout)
    
    def set_quick_range(self, days):
        """Set date range to last N days"""
        self.all_time_checkbox.setChecked(False)
        self.end_date.setDate(QDate.currentDate())
        self.start_date.setDate(QDate.currentDate().addDays(-days))
    
    def set_this_month(self):
        """Set date range to current month"""
        self.all_time_checkbox.setChecked(False)
        today = QDate.currentDate()
        self.start_date.setDate(QDate(today.year(), today.month(), 1))
        self.end_date.setDate(today)
    
    def toggle_date_inputs(self, checked):
        """Toggle date inputs based on checkbox"""
        self.date_container.setEnabled(not checked)
    
    def get_date_range(self):
        """Get selected date range"""
        if self.all_time_checkbox.isChecked():
            return None, None
        return (
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )


# FIX: Create smaller, more compact clickable card widget
class ClickableCard(QFrame):
    """A compact, fully clickable card widget"""
    clicked = Signal()
    
    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 10px;
            }
            QFrame:hover {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
            }
        """)
        
        # Increased height for better spacing and less crowded appearance
        self.setFixedHeight(160)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title - slightly larger
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)

        # Description - slightly larger
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #64748b;
                background: transparent;
                border: none;
                line-height: 1.4;
            }
        """)

        # Arrow indicator
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #94a3b8;
                background: transparent;
                border: none;
                font-weight: 600;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(arrow_label, 0, Qt.AlignRight)
    
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AdminDashboard(QWidget):
    def __init__(self, user, on_logout):
        super().__init__()
        self.user = user
        self.on_logout = on_logout

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
        header.setFixedHeight(90)
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

        title = QLabel("Admin Dashboard")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: 700;
                background: transparent;
            }
        """)

        # Get greeting based on time
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #e8ebf0;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # ================= ACTION CARDS (BETTER SPACING) =================
        cards_layout = QGridLayout()
        cards_layout.setSpacing(24)  # Increased spacing between cards
        cards_layout.setHorizontalSpacing(24)
        cards_layout.setVerticalSpacing(24)

        # Card 1: Manage Projects
        card1 = ClickableCard(
            "Manage Projects",
            "Create and assign projects"
        )
        card1.clicked.connect(self.open_projects)

        # Card 2: Review Submitted Drawings
        card2 = ClickableCard(
            "Review Drawings",
            "Approve or reject submissions"
        )
        card2.clicked.connect(self.open_review)

        # Card 3: Employee Performance Report
        card3 = ClickableCard(
            "Employee Report",
            "Login/logout times & hours"
        )
        card3.clicked.connect(self.download_employee_report)

        # Card 4: Project Status Report
        card4 = ClickableCard(
            "Project Report",
            "Status with payment tracking"
        )
        card4.clicked.connect(self.download_project_report)

        cards_layout.addWidget(card1, 0, 0)
        cards_layout.addWidget(card2, 0, 1)
        cards_layout.addWidget(card3, 0, 2)
        cards_layout.addWidget(card4, 1, 0)

        # Super admin only cards
        if self.user["role"] == "super_admin":
            # Card 5: User Management
            card5 = ClickableCard(
                "User Management",
                "Create and manage accounts"
            )
            card5.clicked.connect(self.open_users)

            # Card 6: Edit Project Template
            card6 = ClickableCard(
                "Project Template",
                "Modify default structure"
            )
            card6.clicked.connect(self.open_template)

            cards_layout.addWidget(card5, 1, 1)
            cards_layout.addWidget(card6, 1, 2)

        content_layout.addLayout(cards_layout)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # ================= PAGE STACK (HIDDEN) =================
        self.pages = QStackedWidget()
        self.pages.hide()

        self.page_projects = AdminProjects()
        self.page_review = AdminReview()
        self.page_template = AdminTemplate()
        self.page_users = SuperAdminUsers(current_user=self.user)

        self.pages.addWidget(self.page_projects)
        self.pages.addWidget(self.page_review)
        self.pages.addWidget(self.page_template)
        self.pages.addWidget(self.page_users)

    # ================= HELPER =================
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

    # ================= ACTIONS =================
    def handle_logout(self):
        fb = FirebaseClient()
        fb.record_logout_time(self.user["user_id"])
        self.on_logout()

    def open_projects(self):
        # Navigate via main window
        main_window = self.window()
        if hasattr(main_window, 'show_projects'):
            main_window.show_projects()

    def open_review(self):
        main_window = self.window()
        if hasattr(main_window, 'show_review'):
            main_window.show_review()

    def open_template(self):
        main_window = self.window()
        if hasattr(main_window, 'show_templates'):
            main_window.show_templates()

    def open_users(self):
        main_window = self.window()
        if hasattr(main_window, 'show_users'):
            main_window.show_users()

    def download_employee_report(self):
        """Generate employee performance report with date range"""
        try:
            # Show modern date range dialog
            dialog = DateRangeDialog(self)
            if dialog.exec() == QDialog.Accepted:
                start_date, end_date = dialog.get_date_range()
                
                # Import and generate report
                from services.employee_performance_report import generate_employee_performance_report
                
                file = generate_employee_performance_report(start_date, end_date)
                
                date_info = ""
                if start_date and end_date:
                    date_info = f"\nDate Range: {start_date} to {end_date}"
                elif start_date:
                    date_info = f"\nFrom: {start_date}"
                elif end_date:
                    date_info = f"\nUntil: {end_date}"
                else:
                    date_info = "\nAll Time Data"
                
                QMessageBox.information(
                    self,
                    "Report Generated",
                    f"Employee performance report created:{date_info}\n\nFile: {file}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate report: {str(e)}"
            )

    def download_project_report(self):
        """Generate project status report"""
        try:
            from services.project_status_report import generate_project_status_report
            
            file = generate_project_status_report()
            
            QMessageBox.information(
                self,
                "Report Generated",
                f"Project status report created with payment tracking!\n\nFile: {file}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate report: {str(e)}"
            )