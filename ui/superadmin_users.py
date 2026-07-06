from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QFrame, QComboBox,
    QListWidgetItem, QDialog, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from services.firebase_client import FirebaseClient
from core.users import UserManager
from core.auth import User
from utils.validators import Validator
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import utils.theme as T
import uuid
import firebase_admin
from firebase_admin import auth


class SuperAdminUsers(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user     = current_user
        self.fb               = FirebaseClient()
        self.user_manager     = UserManager(self.fb)

        self.setStyleSheet(T.app_base())

        from ui.admin_dashboard import make_topbar
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar, back_btn = make_topbar(
            self, current_user, None, show_back=True, back_title="User Management"
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

        # ── LEFT: create user ─────────────────────────────────────────────────
        left_panel = QFrame()
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left = QVBoxLayout(left_panel)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)

        left_hdr = QFrame()
        left_hdr.setFixedHeight(52)
        left_hdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        lh = QHBoxLayout(left_hdr)
        lh.setContentsMargins(16, 0, 16, 0)
        lh_t = QLabel("New User")
        lh_t.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        lh_s = QLabel("Create a staff account")
        lh_s.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: {T.TEXT_SEC}; background: transparent; }}"
        )
        lhv = QVBoxLayout()
        lhv.setSpacing(1)
        lhv.addWidget(lh_t)
        lhv.addWidget(lh_s)
        lh.addLayout(lhv)
        left.addWidget(left_hdr)

        form_area = QWidget()
        form_area.setStyleSheet(f"QWidget {{ background: {T.SURFACE}; }}")
        form = QVBoxLayout(form_area)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(0)

        lbl_style = (
            f"QLabel {{ font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; "
            f"background: transparent; letter-spacing: 0.4px; }}"
        )
        combo_style = (
            f"QComboBox {{ padding: 8px 12px; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; font-size: 13px; background: {T.BG}; color: {T.TEXT}; }}"
            f"QComboBox:focus {{ border-color: {T.ACCENT}; }}"
            f"QComboBox::drop-down {{ border: none; width: 26px; }}"
            f"QComboBox::down-arrow {{ border-left: 4px solid transparent; "
            f"border-right: 4px solid transparent; border-top: 5px solid {T.TEXT_SEC}; "
            f"margin-right: 8px; }}"
            f"QComboBox QAbstractItemView {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; outline: none; }}"
            f"QComboBox QAbstractItemView::item {{ padding: 8px 12px; }}"
            f"QComboBox QAbstractItemView::item:selected {{ background: {T.ACCENT_BG}; color: {T.TEXT}; }}"
        )

        for attr, label, placeholder, echo in [
            ("username", "Username",         "e.g. john.doe",            False),
            ("email",    "Email address",    "user@company.com",          False),
            ("password", "Default Password", "Minimum 6 characters",      True),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(lbl_style)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(T.input_field_flat())
            inp.setMinimumHeight(40)
            if echo:
                inp.setEchoMode(QLineEdit.Password)
            setattr(self, attr, inp)
            form.addWidget(lbl)
            form.addSpacing(5)
            form.addWidget(inp)
            form.addSpacing(14)

        role_lbl = QLabel("Role")
        role_lbl.setStyleSheet(lbl_style)
        self.role = QComboBox()
        self.role.addItems(["Employee", "Admin", "Super Admin"])
        self.role.setStyleSheet(combo_style)
        form.addWidget(role_lbl)
        form.addSpacing(5)
        form.addWidget(self.role)
        form.addSpacing(20)

        self.create_btn = QPushButton("Create User")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setMinimumHeight(40)
        self.create_btn.setStyleSheet(T.btn_primary())
        self.create_btn.clicked.connect(self.handle_create_user)
        form.addWidget(self.create_btn)
        form.addStretch()
        left.addWidget(form_area, 1)

        # ── RIGHT: users list ─────────────────────────────────────────────────
        right_panel = QFrame()
        right_panel.setStyleSheet(
            f"QFrame {{ background: {T.BG}; border: none; }}"
        )
        right = QVBoxLayout(right_panel)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        list_hdr = QFrame()
        list_hdr.setFixedHeight(52)
        list_hdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        rh = QHBoxLayout(list_hdr)
        rh.setContentsMargins(16, 0, 16, 0)
        self.right_title = QLabel("Users")
        self.right_title.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        self.user_count_lbl = QLabel("0")
        self.user_count_lbl.setStyleSheet(
            f"QLabel {{ background: {T.ACCENT_BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 1px 7px; font-size: 11px; font-weight: 600; font-family: monospace; }}"
        )

        # Action buttons in header
        self.change_role_btn = QPushButton("Change Role")
        self.change_role_btn.setCursor(Qt.PointingHandCursor)
        self.change_role_btn.setEnabled(False)
        self.change_role_btn.setFixedHeight(30)
        self.change_role_btn.setStyleSheet(T.btn_secondary())
        self.change_role_btn.clicked.connect(self.handle_change_role)

        self.reset_password_btn = QPushButton("Reset Password")
        self.reset_password_btn.setCursor(Qt.PointingHandCursor)
        self.reset_password_btn.setEnabled(False)
        self.reset_password_btn.setFixedHeight(30)
        self.reset_password_btn.setStyleSheet(T.btn_secondary())
        self.reset_password_btn.clicked.connect(self.handle_reset_password)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setFixedHeight(30)
        self.delete_btn.setStyleSheet(T.btn_danger())
        self.delete_btn.clicked.connect(self.handle_delete_user)

        rh.addWidget(self.right_title)
        rh.addSpacing(8)
        rh.addWidget(self.user_count_lbl)
        rh.addStretch()
        rh.addWidget(self.change_role_btn)
        rh.addSpacing(6)
        rh.addWidget(self.reset_password_btn)
        rh.addSpacing(6)
        rh.addWidget(self.delete_btn)
        right.addWidget(list_hdr)

        # Search box
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        sf = QVBoxLayout(search_frame)
        sf.setContentsMargins(12, 10, 12, 10)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by name or email…")
        self.search_box.setStyleSheet(T.input_field_flat())
        self.search_box.setMinimumHeight(34)
        self.search_box.textChanged.connect(self.filter_users)
        sf.addWidget(self.search_box)
        right.addWidget(search_frame)

        self.users_list = QListWidget()
        self.users_list.setStyleSheet(T.list_widget())
        self.users_list.itemClicked.connect(self.on_user_selected)
        right.addWidget(self.users_list, 1)

        body_layout.addWidget(left_panel)
        body_layout.addWidget(right_panel, 1)
        root_layout.addWidget(body, 1)

        self.load_users()

    def _go_back(self):
        mw = self.window()
        if hasattr(mw, "go_back"):
            mw.go_back()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _make_actor(self):
        if self.current_user:
            return User(
                self.current_user["user_id"], self.current_user["username"],
                self.current_user["email"],   self.current_user["role"]
            )
        return User("admin", "Admin", "admin@sot.com", "super_admin")

    def reset_user_password_firebase(self, user_id, new_password):
        try:
            auth.update_user(user_id, password=new_password)
            return True
        except auth.UserNotFoundError as e:
            raise Exception("User not found in Firebase Authentication.")
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            raise

    # ── Data ──────────────────────────────────────────────────────────────────
    def _make_user_row(self, uid, user):
        """Build a custom widget row for a user: avatar + name/email + role badge."""
        role         = user.get("role", "employee")
        username     = user.get("username", "Unknown")
        email        = user.get("email", "")
        fg, bg       = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
        role_display = role.replace("_", " ").title()
        initials     = "".join(w[0].upper() for w in username.split()[:2])

        row = QWidget()
        row.setStyleSheet(f"QWidget {{ background: transparent; }}")
        h = QHBoxLayout(row)
        h.setContentsMargins(16, 10, 16, 10)
        h.setSpacing(12)

        # Avatar circle
        avatar = QLabel(initials)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"QLabel {{ background: {T.ACCENT_BG}; color: {T.ACCENT}; "
            f"border-radius: 18px; font-size: 12px; font-weight: 700; }}"
        )
        h.addWidget(avatar)

        # Name + email
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        name_lbl = QLabel(username)
        name_lbl.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        email_lbl = QLabel(email)
        email_lbl.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: {T.TEXT_SEC}; background: transparent; }}"
        )
        text_col.addWidget(name_lbl)
        text_col.addWidget(email_lbl)
        h.addLayout(text_col, 1)

        # Role badge pill
        badge = QLabel(role_display)
        badge.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {fg}; border-radius: 4px; "
            f"padding: 3px 8px; font-size: 10px; font-weight: 700; }}"
        )
        h.addWidget(badge)
        return row

    def load_users(self):
        self.users_list.clear()
        try:
            users_data = self.fb.root.child("users").get() or {}
            for uid, user in users_data.items():
                item = QListWidgetItem()
                item.setData(Qt.UserRole, uid)
                item.setData(Qt.UserRole + 1, user.get("role", "employee"))
                item.setSizeHint(QSize(0, 58))
                self.users_list.addItem(item)
                row_widget = self._make_user_row(uid, user)
                self.users_list.setItemWidget(item, row_widget)
            self.user_count_lbl.setText(str(len(users_data)))
            logger.info(f"Loaded {len(users_data)} users")
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to load users: {str(e)}")

    def filter_users(self, text):
        lo = text.lower()
        users_data = self.fb.root.child("users").get() or {}
        uid_list   = list(users_data.keys())
        for i in range(self.users_list.count()):
            item = self.users_list.item(i)
            uid  = item.data(Qt.UserRole)
            user = users_data.get(uid, {})
            haystack = f"{user.get('username','')} {user.get('email','')}".lower()
            item.setHidden(lo not in haystack)

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
                ModernMessageBox.warning(self, "Limit Reached", "Only one Super Admin is allowed.")
                return

        try:
            firebase_user = auth.create_user(email=email, password=password)
            firebase_uid  = firebase_user.uid
            actor         = self._make_actor()
            self.user_manager.create_user(
                actor=actor, user_id=firebase_uid,
                username=username, email=email, role=role
            )
            logger.info(f"User created: {firebase_uid}")
            ModernMessageBox.success(
                self, "User Created",
                f"'{username}' has been created.\n\nEmail: {email}\n"
                f"Password: {password}\n\nThey will be prompted to change their password on first login."
            )
            self.username.clear()
            self.email.clear()
            self.password.clear()
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
        combo_style = (
            f"QComboBox {{ padding: 9px 12px; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; font-size: 13px; background: {T.BG}; color: {T.TEXT}; }}"
            f"QComboBox::drop-down {{ border: none; width: 26px; }}"
            f"QComboBox::down-arrow {{ border-left: 4px solid transparent; "
            f"border-right: 4px solid transparent; border-top: 5px solid {T.TEXT_SEC}; margin-right: 8px; }}"
            f"QComboBox QAbstractItemView {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; outline: none; }}"
            f"QComboBox QAbstractItemView::item {{ padding: 8px 12px; }}"
            f"QComboBox QAbstractItemView::item:selected {{ background: {T.ACCENT_BG}; color: {T.TEXT}; }}"
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Change Role")
        dialog.setModal(True)
        dialog.setMinimumWidth(360)
        dialog.setStyleSheet(
            f"QDialog {{ background: {T.SURFACE}; }} QLabel {{ background: transparent; }}"
        )
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(28, 28, 28, 28)
        dl.setSpacing(12)

        t = QLabel("Change Role")
        t.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {T.TEXT};")
        s = QLabel(f"{user_data.get('username')}  ·  Current: {current_role}")
        s.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")
        dl.addWidget(t)
        dl.addWidget(s)

        combo = QComboBox()
        combo.addItems(["Employee", "Admin"])
        combo.setStyleSheet(combo_style)
        dl.addWidget(combo)

        br = QHBoxLayout(); br.setSpacing(10)
        c = QPushButton("Cancel"); c.setStyleSheet(T.btn_secondary()); c.setMinimumHeight(38); c.clicked.connect(dialog.reject); c.setCursor(Qt.PointingHandCursor)
        s2 = QPushButton("Change Role"); s2.setStyleSheet(T.btn_primary()); s2.setMinimumHeight(38); s2.clicked.connect(dialog.accept); s2.setCursor(Qt.PointingHandCursor)
        br.addStretch(); br.addWidget(c); br.addWidget(s2)
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
        dialog.setStyleSheet(
            f"QDialog {{ background: {T.SURFACE}; }} QLabel {{ background: transparent; }}"
        )
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(28, 28, 28, 28)
        dl.setSpacing(12)

        t = QLabel("Reset Password")
        t.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {T.TEXT};")
        s = QLabel(f"{user_data.get('username')} — they will be required to change it on next login.")
        s.setWordWrap(True)
        s.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")
        dl.addWidget(t)
        dl.addWidget(s)

        lbl = QLabel("New password (min 6 characters)")
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; letter-spacing: 0.4px;")
        dl.addWidget(lbl)
        pw_input = QLineEdit()
        pw_input.setEchoMode(QLineEdit.Password)
        pw_input.setPlaceholderText("New password")
        pw_input.setStyleSheet(T.input_field())
        pw_input.setMinimumHeight(40)
        dl.addWidget(pw_input)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet(
            f"color: {T.DANGER}; background: {T.DANGER_BG}; "
            f"border: 1px solid #FECDD3; border-radius: 4px; padding: 6px 10px; font-size: 12px;"
        )
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
                logger.info(f"Password reset for {user_id}")
                ModernMessageBox.success(
                    self, "Password Reset",
                    f"Password for '{user_data.get('username')}' has been reset.\n\n"
                    "They will be prompted to change it on next login."
                )
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
