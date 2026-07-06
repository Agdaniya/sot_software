# NOTE: Add .returnPressed.connect(submit_button.click) to QLineEdit fields for Enter key support
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QFrame, QComboBox,
    QListWidgetItem, QDialog, QVBoxLayout as QVL, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from services.firebase_client import FirebaseClient
from core.users import UserManager
from core.auth import User
from utils.validators import Validator
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import utils.theme as T
import uuid
import requests
import firebase_admin
from firebase_admin import auth


def _avatar_style(color: str) -> str:
    return f"""
        QLabel {{
            background: {color}22;
            color: {color};
            border-radius: 16px;
            font-size: 13px;
            font-weight: 700;
        }}
    """


class SuperAdminUsers(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user      = current_user
        self.fb                = FirebaseClient()
        self.user_manager      = UserManager(self.fb)
        self.firebase_api_key  = "AIzaSyAXG7m0qlHpg2bETH9bvSYnriYfnEQjzmI"

        self.setStyleSheet(T.app_base())

        root = QHBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        # ── LEFT: create user ─────────────────────────────────────────────────
        left_card = QFrame()
        left_card.setStyleSheet(T.card())
        left = QVBoxLayout(left_card)
        left.setContentsMargins(28, 28, 28, 28)
        left.setSpacing(0)

        left_title = QLabel("New User")
        left_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")
        left_sub   = QLabel("Create a new staff account")
        left_sub.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC}; background: transparent; margin-top: 2px;")
        left.addWidget(left_title)
        left.addWidget(left_sub)
        left.addSpacing(24)

        field_style = T.input_field_flat()

        for attr, label, placeholder, echo in [
            ("username", "Username",         "e.g. john.doe",            False),
            ("email",    "Email address",    "user@company.com",          False),
            ("password", "Default Password", "Minimum 6 characters",      True),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; background: transparent;")
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(field_style)
            inp.setMinimumHeight(40)
            if echo:
                inp.setEchoMode(QLineEdit.Password)
            setattr(self, attr, inp)
            left.addWidget(lbl)
            left.addSpacing(6)
            left.addWidget(inp)
            left.addSpacing(14)

        role_lbl = QLabel("Role")
        role_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; background: transparent;")
        self.role = QComboBox()
        self.role.addItems(["Employee", "Admin", "Super Admin"])
        self.role.setStyleSheet(f"""
            QComboBox {{
                padding: 10px 14px; border: 1.5px solid {T.BORDER};
                border-radius: {T.RADIUS_SM}; font-size: 13px;
                background: {T.BG}; color: {T.TEXT};
            }}
            QComboBox:focus {{ border-color: {T.ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox::down-arrow {{
                border-left: 4px solid transparent; border-right: 4px solid transparent;
                border-top: 5px solid {T.TEXT_SEC}; margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {T.SURFACE}; border: 1px solid {T.BORDER};
                border-radius: {T.RADIUS_SM}; outline: none;
            }}
            QComboBox QAbstractItemView::item {{ padding: 8px 12px; }}
            QComboBox QAbstractItemView::item:selected {{ background: {T.ACCENT_BG}; color: {T.ACCENT}; }}
        """)
        left.addWidget(role_lbl)
        left.addSpacing(6)
        left.addWidget(self.role)
        left.addSpacing(24)

        self.create_btn = QPushButton("Create User")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setMinimumHeight(42)
        self.create_btn.setStyleSheet(T.btn_primary())
        self.create_btn.clicked.connect(self.handle_create_user)
        left.addWidget(self.create_btn)
        left.addStretch()

        # ── RIGHT: users list ─────────────────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(T.card())
        right = QVBoxLayout(right_card)
        right.setContentsMargins(28, 28, 28, 28)
        right.setSpacing(14)

        rh = QHBoxLayout()
        self.right_title = QLabel("Users")
        self.right_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")
        self.user_count_lbl = QLabel("0")
        self.user_count_lbl.setStyleSheet(f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 600;")
        rh.addWidget(self.right_title)
        rh.addStretch()
        rh.addWidget(self.user_count_lbl)
        right.addLayout(rh)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by name or email...")
        self.search_box.setStyleSheet(T.input_field_flat())
        self.search_box.setMinimumHeight(36)
        self.search_box.textChanged.connect(self.filter_users)
        right.addWidget(self.search_box)

        self.users_list = QListWidget()
        self.users_list.setStyleSheet(T.list_widget())
        self.users_list.itemClicked.connect(self.on_user_selected)
        right.addWidget(self.users_list)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.change_role_btn = QPushButton("Change Role")
        self.change_role_btn.setCursor(Qt.PointingHandCursor)
        self.change_role_btn.setEnabled(False)
        self.change_role_btn.setMinimumHeight(36)
        self.change_role_btn.setStyleSheet(T.btn_secondary())
        self.change_role_btn.clicked.connect(self.handle_change_role)

        self.reset_password_btn = QPushButton("Reset Password")
        self.reset_password_btn.setCursor(Qt.PointingHandCursor)
        self.reset_password_btn.setEnabled(False)
        self.reset_password_btn.setMinimumHeight(36)
        self.reset_password_btn.setStyleSheet(T.btn_secondary())
        self.reset_password_btn.clicked.connect(self.handle_reset_password)

        self.delete_btn = QPushButton("Delete User")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.setStyleSheet(T.btn_danger())
        self.delete_btn.clicked.connect(self.handle_delete_user)

        action_row.addWidget(self.change_role_btn)
        action_row.addWidget(self.reset_password_btn)
        action_row.addWidget(self.delete_btn)
        right.addLayout(action_row)

        root.addWidget(left_card, 1)
        root.addWidget(right_card, 2)

        self.load_users()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _role_color(self, role: str) -> str:
        return T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))[0]

    def _make_actor(self):
        if self.current_user:
            return User(self.current_user["user_id"], self.current_user["username"],
                        self.current_user["email"],   self.current_user["role"])
        return User("admin", "Admin", "admin@sot.com", "super_admin")

    def reset_user_password_firebase(self, user_id, new_password):
        try:
            auth.update_user(user_id, password=new_password)
            logger.info(f"Password reset for {user_id}")
            return True
        except auth.UserNotFoundError as e:
            logger.warning(f"User {user_id} not found in Firebase Auth: {str(e)}")
            raise Exception("User not found in Firebase Authentication.")
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise

    # ── Data ──────────────────────────────────────────────────────────────────
    def load_users(self):
        self.users_list.clear()
        try:
            users_data = self.fb.root.child("users").get() or {}
            for uid, user in users_data.items():
                role         = user.get("role", "employee")
                role_display = role.replace("_", " ").title()
                fg, _        = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
                item_text    = f"{user.get('username', 'Unknown')}  [{role_display}]\n{user.get('email', '')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, uid)
                item.setData(Qt.UserRole + 1, role)
                self.users_list.addItem(item)
            self.user_count_lbl.setText(str(len(users_data)))
            logger.info(f"Loaded {len(users_data)} users")
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load users: {str(e)}")

    def filter_users(self, text):
        text_lower = text.lower()
        for i in range(self.users_list.count()):
            item = self.users_list.item(i)
            item.setHidden(text_lower not in item.text().lower())

    def on_user_selected(self, item):
        user_id   = item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        is_super  = user_data and user_data.get("role") == "super_admin"
        self.reset_password_btn.setEnabled(True)
        self.change_role_btn.setEnabled(not is_super)
        self.delete_btn.setEnabled(not is_super)

    # ── Actions ───────────────────────────────────────────────────────────────
    def handle_create_user(self):
        username  = self.username.text().strip()
        email     = self.email.text().strip()
        password  = self.password.text().strip()
        role_text = self.role.currentText()
        role      = {"Employee": "employee", "Admin": "admin", "Super Admin": "super_admin"}[role_text]

        ok, err = Validator.validate_username(username)
        if not ok: ModernMessageBox.warning(self, "Validation", err); return
        ok, err = Validator.validate_email(email)
        if not ok: ModernMessageBox.warning(self, "Validation", err); return
        ok, err = Validator.validate_password(password)
        if not ok: ModernMessageBox.warning(self, "Validation", err); return

        if role == "super_admin":
            users = self.fb.root.child("users").get() or {}
            if sum(1 for u in users.values() if u.get("role") == "super_admin") >= 1:
                ModernMessageBox.warning(self, "Limit Reached", "Only one Super Admin is allowed."); return

        try:
            firebase_user = auth.create_user(email=email, password=password)
            firebase_uid  = firebase_user.uid
            actor         = self._make_actor()
            self.user_manager.create_user(actor=actor, user_id=firebase_uid,
                                          username=username, email=email, role=role)
            logger.info(f"User created: {firebase_uid}")
            ModernMessageBox.success(
                self, "User Created",
                f"'{username}' has been created.\n\nEmail: {email}\nPassword: {password}\n\nThey will be prompted to change their password on first login."
            )
            self.username.clear(); self.email.clear(); self.password.clear()
            self.role.setCurrentIndex(0)
            self.load_users()
        except PermissionError as e:
            ModernMessageBox.error(self, "Permission Denied", str(e))
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to create user: {str(e)}")

    def handle_change_role(self):
        current_item = self.users_list.currentItem()
        if not current_item: return
        user_id   = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        if not user_data:
            ModernMessageBox.warning(self, "Error", "User not found"); return
        if user_data.get("role") == "super_admin":
            ModernMessageBox.warning(self, "Protected", "Super Admin role cannot be changed."); return

        current_role = user_data.get("role", "employee").replace("_", " ").title()
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Role")
        dialog.setModal(True)
        dialog.setMinimumWidth(360)
        dialog.setStyleSheet(f"QDialog {{ background: {T.SURFACE}; }} QLabel {{ background: transparent; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(28, 28, 28, 28)
        dl.setSpacing(16)
        dl.addWidget(QLabel(f"Change role for: {user_data.get('username')}"))
        lbl = QLabel(f"Current role: {current_role}")
        lbl.setStyleSheet(f"color: {T.TEXT_SEC}; font-size: 12px;")
        dl.addWidget(lbl)
        combo = QComboBox()
        combo.addItems(["Employee", "Admin"])
        combo.setStyleSheet(f"""
            QComboBox {{ padding: 9px 12px; border: 1.5px solid {T.BORDER}; border-radius: {T.RADIUS_SM}; font-size: 13px; background: {T.BG}; color: {T.TEXT}; }}
            QComboBox::drop-down {{ border: none; width: 28px; }}
            QComboBox::down-arrow {{ border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {T.TEXT_SEC}; margin-right: 8px; }}
            QComboBox QAbstractItemView {{ background: {T.SURFACE}; border: 1px solid {T.BORDER}; outline: none; }}
            QComboBox QAbstractItemView::item {{ padding: 8px 12px; }}
            QComboBox QAbstractItemView::item:selected {{ background: {T.ACCENT_BG}; color: {T.ACCENT}; }}
        """)
        dl.addWidget(combo)
        br = QHBoxLayout(); br.setSpacing(10)
        c = QPushButton("Cancel"); c.setStyleSheet(T.btn_secondary()); c.setMinimumHeight(38); c.clicked.connect(dialog.reject); c.setCursor(Qt.PointingHandCursor)
        s = QPushButton("Change Role"); s.setStyleSheet(T.btn_primary()); s.setMinimumHeight(38); s.clicked.connect(dialog.accept); s.setCursor(Qt.PointingHandCursor)
        br.addStretch(); br.addWidget(c); br.addWidget(s)
        dl.addLayout(br)

        if dialog.exec() == QDialog.Accepted:
            new_role = {"Employee": "employee", "Admin": "admin"}[combo.currentText()]
            try:
                self.user_manager.change_role(self._make_actor(), user_id, new_role)
                logger.info(f"Changed role for {user_id} to {new_role}")
                self.load_users()
            except Exception as e:
                logger.error(f"Error changing role: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to change role: {str(e)}")

    def handle_reset_password(self):
        current_item = self.users_list.currentItem()
        if not current_item: return
        user_id   = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        if not user_data:
            ModernMessageBox.warning(self, "Error", "User not found"); return

        dialog = QDialog(self)
        dialog.setWindowTitle("Reset Password")
        dialog.setModal(True)
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet(f"QDialog {{ background: {T.SURFACE}; }} QLabel {{ background: transparent; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(28, 28, 28, 28)
        dl.setSpacing(14)
        t = QLabel(f"Reset password for {user_data.get('username')}")
        t.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT};")
        dl.addWidget(t)
        s = QLabel("They will be required to change it on next login.")
        s.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")
        dl.addWidget(s)
        lbl = QLabel("New password (min 6 characters)")
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC};")
        dl.addWidget(lbl)
        pw_input = QLineEdit()
        pw_input.setEchoMode(QLineEdit.Password)
        pw_input.setPlaceholderText("New password")
        pw_input.setStyleSheet(T.input_field())
        pw_input.setMinimumHeight(40)
        dl.addWidget(pw_input)
        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {T.DANGER}; background: {T.DANGER_BG}; border-radius: 4px; padding: 6px; font-size: 12px;")
        err_lbl.hide()
        dl.addWidget(err_lbl)
        br = QHBoxLayout(); br.setSpacing(10)
        c = QPushButton("Cancel"); c.setStyleSheet(T.btn_secondary()); c.setMinimumHeight(38); c.clicked.connect(dialog.reject); c.setCursor(Qt.PointingHandCursor)
        r = QPushButton("Reset Password"); r.setStyleSheet(T.btn_primary()); r.setMinimumHeight(38); r.setCursor(Qt.PointingHandCursor)
        br.addStretch(); br.addWidget(c); br.addWidget(r)
        dl.addLayout(br)

        def do_reset():
            pw = pw_input.text().strip()
            ok, err = Validator.validate_password(pw)
            if not ok:
                err_lbl.setText(err); err_lbl.show(); return
            dialog.new_password = pw
            dialog.accept()

        r.clicked.connect(do_reset)
        pw_input.returnPressed.connect(do_reset)
        dialog.new_password = None

        if dialog.exec() == QDialog.Accepted and dialog.new_password:
            try:
                self.reset_user_password_firebase(user_id, dialog.new_password)
                self.user_manager.force_password_reset(self._make_actor(), user_id)
                logger.info(f"Password reset for user {user_id}")
                ModernMessageBox.success(self, "Password Reset",
                    f"Password for '{user_data.get('username')}' has been reset.\n\nThey will be prompted to change it on next login.")
            except Exception as e:
                logger.error(f"Error resetting password: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to reset password: {str(e)}")

    def handle_delete_user(self):
        current_item = self.users_list.currentItem()
        if not current_item: return
        user_id   = current_item.data(Qt.UserRole)
        user_data = self.fb.get_user(user_id)
        if not user_data:
            ModernMessageBox.warning(self, "Error", "User not found"); return
        if user_data.get("role") == "super_admin":
            ModernMessageBox.warning(self, "Protected", "Super Admin account cannot be deleted."); return

        if ModernMessageBox.confirm_delete(self, user_data.get("username", "this user")):
            try:
                try:
                    auth.delete_user(user_id)
                except Exception:
                    pass
                self.user_manager.delete_user(self._make_actor(), user_id)
                logger.info(f"Deleted user {user_id}")
                self.change_role_btn.setEnabled(False)
                self.reset_password_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.load_users()
            except Exception as e:
                logger.error(f"Error deleting user: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to delete user: {str(e)}")
