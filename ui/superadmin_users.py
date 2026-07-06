# NOTE: Add .returnPressed.connect(submit_button.click) to QLineEdit fields for Enter key support
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QFrame, QComboBox, 
    QListWidgetItem, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from services.firebase_client import FirebaseClient
from core.users import UserManager
from core.auth import User
from utils.validators import Validator
from utils.logger import logger
import uuid
import requests
import firebase_admin
from firebase_admin import auth


class SuperAdminUsers(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.fb = FirebaseClient()
        self.user_manager = UserManager(self.fb)
        
        # Firebase Web API key (for creating users)
        self.firebase_api_key = "AIzaSyAXG7m0qlHpg2bETH9bvSYnriYfnEQjzmI"

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

        # ===== LEFT: CREATE USER =====
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
        left.setSpacing(20)
        
        # Header with icon
        header_layout = QHBoxLayout()
        icon_label = QLabel("👤")
        icon_label.setStyleSheet("QLabel { font-size: 20px; background: transparent; }")
        
        left_title = QLabel("Create New User")
        left_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(left_title)
        header_layout.addStretch()
        left.addLayout(header_layout)

        # Username field
        username_label = QLabel("Username *")
        username_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username (3-50 characters)")
        self.username.setStyleSheet("""
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

        # Email field
        email_label = QLabel("Email *")
        email_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("user@company.com")
        self.email.setStyleSheet("""
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

        # Password field
        password_label = QLabel("Default Password *")
        password_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Minimum 6 characters")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("""
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

        # Role dropdown
        role_label = QLabel("Role *")
        role_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        self.role = QComboBox()
        self.role.addItems(["Employee", "Admin", "Super Admin"])
        self.role.setStyleSheet("""
            QComboBox {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #1e293b;
            }
            QComboBox:focus {
                background: #e2e8f0;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748b;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #f1f5f9;
            }
            QComboBox QAbstractItemView::item:selected {
                background: #1e40af;
                color: white;
            }
        """)

        left.addWidget(username_label)
        left.addWidget(self.username)
        left.addWidget(email_label)
        left.addWidget(self.email)
        left.addWidget(password_label)
        left.addWidget(self.password)
        left.addWidget(role_label)
        left.addWidget(self.role)

        # Create button
        self.create_btn = QPushButton("👤  Create User")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background: #1e3a8a;
            }
        """)
        self.create_btn.clicked.connect(self.handle_create_user)

        left.addWidget(self.create_btn)
        left.addStretch()

        # ===== RIGHT: USERS LIST =====
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
        right.setSpacing(16)

        # Header with icon
        right_header_layout = QHBoxLayout()
        users_icon = QLabel("👥")
        users_icon.setStyleSheet("QLabel { font-size: 20px; background: transparent; }")
        
        self.right_title = QLabel("Existing Users")
        self.right_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        right_header_layout.addWidget(users_icon)
        right_header_layout.addWidget(self.right_title)
        right_header_layout.addStretch()
        right.addLayout(right_header_layout)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search users...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                padding: 10px 16px;
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
        self.search_box.textChanged.connect(self.filter_users)
        right.addWidget(self.search_box)

        # Users list
        self.users_list = QListWidget()
        self.users_list.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 4px;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 14px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 8px;
                background: #f8fafc;
                color: #1e293b;
                font-size: 13px;
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
        self.users_list.itemClicked.connect(self.on_user_selected)
        right.addWidget(self.users_list)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.change_role_btn = QPushButton("🔄 Change Role")
        self.change_role_btn.setCursor(Qt.PointingHandCursor)
        self.change_role_btn.setEnabled(False)
        self.change_role_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #1e293b;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover:enabled {
                background: #e2e8f0;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.change_role_btn.clicked.connect(self.handle_change_role)

        self.reset_password_btn = QPushButton("🔑 Reset Password")
        self.reset_password_btn.setCursor(Qt.PointingHandCursor)
        self.reset_password_btn.setEnabled(False)
        self.reset_password_btn.setStyleSheet("""
            QPushButton {
                background: #fef3c7;
                color: #92400e;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover:enabled {
                background: #fde68a;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.reset_password_btn.clicked.connect(self.handle_reset_password)

        self.delete_btn = QPushButton("🗑️ Delete User")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #fecaca;
                color: #991b1b;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover:enabled {
                background: #fca5a5;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        self.delete_btn.clicked.connect(self.handle_delete_user)

        action_layout.addWidget(self.change_role_btn)
        action_layout.addWidget(self.reset_password_btn)
        action_layout.addWidget(self.delete_btn)
        right.addLayout(action_layout)

        root.addWidget(left_frame, 1)
        root.addWidget(right_frame, 2)

        self.load_users()

    def reset_user_password_firebase(self, user_id, new_password):
        """
        Reset user password in Firebase Authentication using Admin SDK
        
        Args:
            user_id: Firebase user UID (should be the same as our database user_id)
            new_password: New password to set
            
        Returns:
            bool: True if successful
        """
        try:
            # FIX: The user_id should already be the Firebase Auth UID since we store it that way
            # when creating users. Just update the password directly.
            auth.update_user(
                user_id,
                password=new_password
            )
            
            logger.info(f"Password reset successful for user {user_id}")
            return True
            
        except auth.UserNotFoundError as e:
            # If user not found in Auth, it may have been deleted
            # Still allow the database first_login flag to be set
            logger.warning(f"User {user_id} not found in Firebase Auth: {str(e)}")
            raise Exception(f"User not found in Firebase Authentication. The account may have been deleted.")
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise

    def handle_create_user(self):
        """Handle user creation"""
        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text().strip()
        role_text = self.role.currentText()
        
        role_mapping = {
            "Employee": "employee",
            "Admin": "admin",
            "Super Admin": "super_admin"
        }
        role = role_mapping[role_text]
        
        # Validate inputs
        is_valid, error = Validator.validate_username(username)
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        is_valid, error = Validator.validate_email(email)
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        is_valid, error = Validator.validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        # FIX: Prevent creating more than one super admin
        if role == "super_admin":
            # Check if a super admin already exists
            users = self.fb.root.child("users").get() or {}
            super_admin_count = sum(1 for u in users.values() if u.get("role") == "super_admin")
            
            if super_admin_count >= 1:
                QMessageBox.warning(
                    self,
                    "Cannot Create Super Admin",
                    "Only one Super Admin account is allowed in the system.\n\nA Super Admin already exists."
                )
                return
        
        try:
            # Create user in Firebase Authentication using Admin SDK
            firebase_user = auth.create_user(
                email=email,
                password=password
            )
            
            firebase_uid = firebase_user.uid
            
            # Create actor user object
            if self.current_user:
                actor = User(
                    user_id=self.current_user['user_id'],
                    username=self.current_user['username'],
                    email=self.current_user['email'],
                    role=self.current_user['role']
                )
            else:
                actor = User("admin", "Admin", "admin@sot.com", "super_admin")
            
            # Create user in database
            self.user_manager.create_user(
                actor=actor,
                user_id=firebase_uid,  # Use Firebase UID as user_id
                username=username,
                email=email,
                role=role
            )
            
            logger.info(f"User created successfully: {firebase_uid}")
            
            QMessageBox.information(
                self,
                "Success",
                f"User '{username}' created successfully!\n\nDefault credentials:\nEmail: {email}\nPassword: {password}\n\nUser will be prompted to change password on first login."
            )
            
            # Clear form
            self.username.clear()
            self.email.clear()
            self.password.clear()
            self.role.setCurrentIndex(0)
            
            # Reload users list
            self.load_users()
            
        except PermissionError as e:
            logger.error(f"Permission denied creating user: {str(e)}")
            QMessageBox.critical(self, "Permission Denied", str(e))
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

    def load_users(self):
        """Load all users from Firebase"""
        self.users_list.clear()
        
        try:
            users_data = self.fb.root.child("users").get() or {}
            
            for uid, user in users_data.items():
                role_display = user.get('role', 'employee').replace('_', ' ').title()
                
                # Create list item with user info
                item_text = f"{user.get('username', 'Unknown')}\n{user.get('email', '')}\nRole: {role_display}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, uid)
                self.users_list.addItem(item)
            
            # Update count
            self.right_title.setText(f"Existing Users ({len(users_data)})")
            
            logger.info(f"Loaded {len(users_data)} users")
            
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")

    def filter_users(self, text):
        """Filter users list based on search text"""
        text_lower = text.lower()
        for i in range(self.users_list.count()):
            item = self.users_list.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def on_user_selected(self, item):
        """Enable action buttons when user is selected"""
        user_id = item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        
        # Check if this is the super admin
        is_super_admin = user_data and user_data.get('role') == 'super_admin'
        
        # Password reset is allowed for everyone
        self.reset_password_btn.setEnabled(True)
        
        # Role change and delete are NOT allowed for super admin
        self.change_role_btn.setEnabled(not is_super_admin)
        self.delete_btn.setEnabled(not is_super_admin)

    def handle_change_role(self):
        """Change selected user's role"""
        current_item = self.users_list.currentItem()
        if not current_item:
            return
        
        user_id = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        
        if not user_data:
            QMessageBox.warning(self, "Error", "User not found")
            return
        
        # FIX: Prevent changing super admin's role
        if user_data.get('role') == 'super_admin':
            QMessageBox.warning(
                self,
                "Cannot Change Super Admin Role",
                "The Super Admin's role cannot be changed.\n\nThis is a protected system account."
            )
            return
        
        current_role = user_data.get('role', 'employee').replace('_', ' ').title()
        
        # FIX: Remove "Super Admin" from available roles - only one super admin allowed
        roles = ["Employee", "Admin"]
        new_role, ok = QInputDialog.getItem(
            self,
            "Change Role",
            f"Select new role for {user_data.get('username')}:\n(Current: {current_role})",
            roles,
            0,
            False
        )
        
        if ok and new_role:
            role_mapping = {
                "Employee": "employee",
                "Admin": "admin"
            }
            
            try:
                if self.current_user:
                    actor = User(
                        user_id=self.current_user['user_id'],
                        username=self.current_user['username'],
                        email=self.current_user['email'],
                        role=self.current_user['role']
                    )
                else:
                    actor = User("admin", "Admin", "admin@sot.com", "super_admin")
                
                self.user_manager.change_role(actor, user_id, role_mapping[new_role])
                
                logger.info(f"Changed role for user {user_id} to {role_mapping[new_role]}")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Role updated to {new_role}"
                )
                
                self.load_users()
                
            except Exception as e:
                logger.error(f"Error changing role: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to change role: {str(e)}")

    def handle_reset_password(self):
        """Reset password to default for selected user"""
        current_item = self.users_list.currentItem()
        if not current_item:
            return
        
        user_id = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        
        if not user_data:
            QMessageBox.warning(self, "Error", "User not found")
            return
        
        # Ask for new default password
        new_password, ok = QInputDialog.getText(
            self,
            "Reset Password",
            f"Enter new default password for {user_data.get('username')}:\n(Minimum 6 characters)",
            QLineEdit.Password
        )
        
        if ok and new_password:
            # Validate password
            is_valid, error = Validator.validate_password(new_password)
            if not is_valid:
                QMessageBox.warning(self, "Validation Error", error)
                return
            
            reply = QMessageBox.question(
                self,
                "Confirm Password Reset",
                f"Reset password for {user_data.get('username')} to the entered password?\n\nThey will be required to change it on next login.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Reset password in Firebase Authentication using Admin SDK
                    self.reset_user_password_firebase(user_id, new_password)
                    
                    # Set first_login flag in database
                    if self.current_user:
                        actor = User(
                            user_id=self.current_user['user_id'],
                            username=self.current_user['username'],
                            email=self.current_user['email'],
                            role=self.current_user['role']
                        )
                    else:
                        actor = User("admin", "Admin", "admin@sot.com", "super_admin")
                    
                    self.user_manager.force_password_reset(actor, user_id)
                    
                    logger.info(f"Password reset for user {user_id}")
                    
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Password reset successfully!\n\nNew password: {new_password}\n\nUser will be prompted to change it on next login."
                    )
                    
                except Exception as e:
                    logger.error(f"Error resetting password: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Failed to reset password: {str(e)}")

    def handle_delete_user(self):
        """Delete selected user"""
        current_item = self.users_list.currentItem()
        if not current_item:
            return
        
        user_id = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        
        if not user_data:
            QMessageBox.warning(self, "Error", "User not found")
            return
        
        # FIX: Prevent deleting the super admin account
        if user_data.get('role') == 'super_admin':
            QMessageBox.warning(
                self,
                "Cannot Delete Super Admin",
                "The Super Admin account cannot be deleted.\n\nThis is a protected system account."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {user_data.get('username')}?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.current_user:
                    actor = User(
                        user_id=self.current_user['user_id'],
                        username=self.current_user['username'],
                        email=self.current_user['email'],
                        role=self.current_user['role']
                    )
                else:
                    actor = User("admin", "Admin", "admin@sot.com", "super_admin")
                
                # Delete from Firebase Auth
                try:
                    auth.delete_user(user_id)
                except:
                    pass  # User might not exist in auth
                
                # Delete from database
                self.user_manager.delete_user(actor, user_id)
                
                logger.info(f"Deleted user {user_id}")
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"User '{user_data.get('username')}' deleted successfully"
                )
                
                # Disable action buttons
                self.change_role_btn.setEnabled(False)
                self.reset_password_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
                self.load_users()
                
            except Exception as e:
                logger.error(f"Error deleting user: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")