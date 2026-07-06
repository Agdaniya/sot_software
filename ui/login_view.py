from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from services.auth_client import AuthClient


class LoginView(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()

        # Adaptive styling for light/dark mode
        self.setStyleSheet("""
            QWidget {
                background: #e8ebf0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---------- CENTER CARD ----------
        card = QFrame()
        card.setFixedWidth(480)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: none;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(48, 48, 48, 48)

        # ---------- TITLE ----------
        title = QLabel("SOT")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 40px;
                font-weight: 700;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)

        subtitle = QLabel("Staff Project Tracker")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 400;
                color: #94a3b8;
                background: transparent;
                border: none;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        # ---------- EMAIL ----------
        email_label = QLabel("Email")
        email_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setStyleSheet("""
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
        self.email_input.setMinimumHeight(44)

        # ---------- PASSWORD ----------
        password_label = QLabel("Password")
        password_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
                border: none;
            }
        """)

        password_container = QFrame()
        password_container.setStyleSheet("""
            QFrame {
                background: #f1f5f9;
                border-radius: 8px;
            }
        """)
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: none;
                background: transparent;
                font-size: 14px;
                color: #1e293b;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        self.password_input.setMinimumHeight(44)

        self.toggle_password_btn = QPushButton("👁️")
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.setFixedSize(44, 44)
        self.toggle_password_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 20px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background: #e2e8f0;
                border-radius: 6px;
            }
        """)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        self.password_visible = False

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_btn)

        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        layout.addSpacing(8)
        layout.addWidget(password_label)
        layout.addWidget(password_container)

        # ---------- SIGN IN BUTTON ----------
        self.login_button = QPushButton("Sign In")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setMinimumHeight(48)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1e3a8a;
            }
            QPushButton:pressed {
                background: #1e3a8a;
            }
        """)

        layout.addSpacing(8)
        layout.addWidget(self.login_button)

        # ---------- ERROR MESSAGE ----------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            QLabel {
                color: #dc2626;
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        # ---------- CENTER ----------
        main_layout.addStretch()
        main_layout.addWidget(card, 0, Qt.AlignCenter)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # ---------- AUTH ----------
        self.auth = AuthClient("AIzaSyAXG7m0qlHpg2bETH9bvSYnriYfnEQjzmI")

        # ---------- EVENTS ----------
        self.login_button.clicked.connect(self.handle_login)
        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁️")
            self.password_visible = False
        else:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
            self.password_visible = True

    def show_password_change_dialog(self, user):
        """
        FIX #3: Password change dialog with FIXED STYLING
        Ensures proper contrast in both light and dark modes
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Password Change Required")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        # FIX #3: EXPLICIT background and text colors that work everywhere
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Title with proper color
        title = QLabel("🔒 Change Your Password")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #1e293b;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)
        
        # Message with proper color
        message = QLabel(
            f"Welcome, {user.get('username', 'User')}!\n\n"
            "For security reasons, you must change your password before continuing."
        )
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #475569;
                line-height: 1.5;
                background-color: transparent;
            }
        """)
        layout.addWidget(message)
        
        # New password field
        new_pass_label = QLabel("New Password (minimum 6 characters)")
        new_pass_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #1e293b;
                background-color: transparent;
            }
        """)
        layout.addWidget(new_pass_label)
        
        new_pass_input = QLineEdit()
        new_pass_input.setEchoMode(QLineEdit.Password)
        new_pass_input.setPlaceholderText("Enter new password")
        new_pass_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 2px solid #1e40af;
                background-color: #f8fafc;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        layout.addWidget(new_pass_input)
        
        # Confirm password field
        confirm_pass_label = QLabel("Confirm New Password")
        confirm_pass_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #1e293b;
                background-color: transparent;
            }
        """)
        layout.addWidget(confirm_pass_label)
        
        confirm_pass_input = QLineEdit()
        confirm_pass_input.setEchoMode(QLineEdit.Password)
        confirm_pass_input.setPlaceholderText("Re-enter new password")
        confirm_pass_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #1e293b;
            }
            QLineEdit:focus {
                border: 2px solid #1e40af;
                background-color: #f8fafc;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        layout.addWidget(confirm_pass_input)
        
        # Error label with proper contrast
        error_label = QLabel("")
        error_label.setStyleSheet("""
            QLabel {
                color: #dc2626;
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
        """)
        error_label.hide()
        layout.addWidget(error_label)
        
        # Buttons with explicit colors
        button_box = QDialogButtonBox()
        change_btn = QPushButton("Change Password")
        change_btn.setCursor(Qt.PointingHandCursor)
        change_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e3a8a;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #1e293b;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        button_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        button_box.addButton(change_btn, QDialogButtonBox.AcceptRole)
        layout.addWidget(button_box)
        
        # Validation function
        def validate_and_accept():
            new_pass = new_pass_input.text().strip()
            confirm_pass = confirm_pass_input.text().strip()
            
            if not new_pass:
                error_label.setText("Password cannot be empty")
                error_label.show()
                return
            
            if len(new_pass) < 6:
                error_label.setText("Password must be at least 6 characters")
                error_label.show()
                return
            
            if new_pass != confirm_pass:
                error_label.setText("Passwords do not match")
                error_label.show()
                return
            
            dialog.new_password = new_pass
            dialog.accept()
        
        change_btn.clicked.connect(validate_and_accept)
        cancel_btn.clicked.connect(dialog.reject)
        new_pass_input.returnPressed.connect(validate_and_accept)
        confirm_pass_input.returnPressed.connect(validate_and_accept)
        
        dialog.new_password = None
        
        if dialog.exec() == QDialog.Accepted:
            return dialog.new_password
        return None

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            self.error_label.setText("Email and password are required.")
            self.error_label.show()
            return

        try:
            user_data = self.auth.sign_in(email, password)

            from services.firebase_client import FirebaseClient
            fb = FirebaseClient()

            users = fb.root.child("users").get() or {}
            current_user = None

            for uid, user in users.items():
                if user.get("email") == user_data["email"]:
                    current_user = user
                    break

            if not current_user:
                self.error_label.setText("User profile not found.")
                self.error_label.show()
                return

            # Record login time
            fb.record_login_time(current_user["user_id"])

            self.error_label.hide()
            
            # Check if password change is required
            if current_user.get("first_login", False):
                # Show password change dialog
                new_password = self.show_password_change_dialog(current_user)
                if new_password:
                    # Update password in Firebase Auth and clear first_login flag
                    try:
                        import firebase_admin
                        from firebase_admin import auth as firebase_auth
                        
                        firebase_auth.update_user(
                            current_user["user_id"],
                            password=new_password
                        )
                        
                        # Clear first_login flag
                        current_user["first_login"] = False
                        fb.save_user(current_user)
                        
                        from utils.modern_dialogs import ModernMessageBox
                        ModernMessageBox.success(
                            self,
                            "Password Changed",
                            "Your password has been changed successfully!"
                        )
                    except Exception as e:
                        from utils.modern_dialogs import ModernMessageBox
                        ModernMessageBox.error(
                            self,
                            "Error",
                            f"Failed to update password: {str(e)}"
                        )
                        return
                else:
                    # User cancelled password change
                    return
            
            self.login_success.emit(current_user)

        except Exception:
            self.error_label.setText("Invalid credentials. Please try again.")
            self.error_label.show()