from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QHBoxLayout, QDialog
)
from PySide6.QtCore import Qt, Signal
from services.auth_client import AuthClient
import utils.theme as T


class LoginView(QWidget):
    login_success = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"QWidget {{ background: {T.BG}; font-family: {T.FONT}; }}")

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT accent panel ─────────────────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(f"QFrame {{ background: {T.ACCENT}; border: none; }}")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(56, 0, 56, 0)
        left_layout.setSpacing(0)
        left_layout.addStretch()

        mono_tag = QLabel("Staff Operations Tracker")
        mono_tag.setStyleSheet(
            "QLabel { color: rgba(255,255,255,0.35); font-size: 10px; "
            "font-family: 'Courier New', monospace; letter-spacing: 3px; "
            "text-transform: uppercase; background: transparent; margin-bottom: 40px; }"
        )

        brand = QLabel("SOT")
        brand.setStyleSheet(
            "QLabel { color: white; font-size: 96px; font-weight: 800; "
            "background: transparent; line-height: 1; margin-bottom: 20px; }"
        )

        divider = QFrame()
        divider.setFixedSize(48, 1)
        divider.setStyleSheet("background: rgba(255,255,255,0.20); border: none;")

        caption = QLabel(
            "Manage architectural projects,\n"
            "track drawing workflows,\n"
            "and coordinate team reviews."
        )
        caption.setStyleSheet(
            "QLabel { color: rgba(255,255,255,0.55); font-size: 14px; "
            "line-height: 1.8; background: transparent; margin-top: 28px; }"
        )

        version = QLabel("SOT Architecture Management · v2.4")
        version.setStyleSheet(
            "QLabel { color: rgba(255,255,255,0.20); font-size: 10px; "
            "font-family: 'Courier New', monospace; background: transparent; margin-top: 60px; }"
        )

        left_layout.addWidget(mono_tag)
        left_layout.addWidget(brand)
        left_layout.addWidget(divider)
        left_layout.addWidget(caption)
        left_layout.addStretch()
        left_layout.addWidget(version)
        left_layout.addSpacing(40)

        # ── RIGHT login form ──────────────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(f"QFrame {{ background: {T.BG}; border: none; }}")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch()

        # Card
        card = QFrame()
        card.setFixedWidth(360)
        card.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-radius: {T.RADIUS_XL}; }}"
        )

        form = QVBoxLayout(card)
        form.setContentsMargins(44, 44, 44, 44)
        form.setSpacing(0)

        heading = QLabel("Welcome back")
        heading.setStyleSheet(
            f"QLabel {{ font-size: 22px; font-weight: 600; color: {T.TEXT}; "
            f"background: transparent; letter-spacing: -0.3px; }}"
        )

        sub = QLabel("Sign in to your account")
        sub.setStyleSheet(
            f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; "
            f"background: transparent; margin-top: 4px; }}"
        )

        form.addWidget(heading)
        form.addWidget(sub)
        form.addSpacing(28)

        # Email
        email_lbl = self._field_label("Email")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("you@company.com")
        self.email_input.setMinimumHeight(40)
        self.email_input.setStyleSheet(T.input_field())

        form.addWidget(email_lbl)
        form.addSpacing(6)
        form.addWidget(self.email_input)
        form.addSpacing(16)

        # Password
        pass_lbl = self._field_label("Password")

        pass_row = QFrame()
        pass_row.setStyleSheet(
            f"QFrame {{ border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS_SM}; background: {T.SURFACE}; }}"
        )
        pass_row_layout = QHBoxLayout(pass_row)
        pass_row_layout.setContentsMargins(0, 0, 6, 0)
        pass_row_layout.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(38)
        self.password_input.setStyleSheet(
            f"QLineEdit {{ border: none; padding: 8px 12px; font-size: 13px; "
            f"background: transparent; color: {T.TEXT}; }}"
            f"QLineEdit::placeholder {{ color: {T.TEXT_HINT}; }}"
        )
        self.password_visible = False

        self.toggle_password_btn = QPushButton("Show")
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.setFixedHeight(26)
        self.toggle_password_btn.setStyleSheet(
            f"QPushButton {{ background: {T.BG}; color: {T.TEXT_SEC}; "
            f"border: none; border-radius: 4px; font-size: 11px; "
            f"font-weight: 600; padding: 0 10px; }}"
            f"QPushButton:hover {{ background: {T.BORDER_SOLID}; }}"
        )
        self.toggle_password_btn.clicked.connect(self._toggle_password)

        pass_row_layout.addWidget(self.password_input)
        pass_row_layout.addWidget(self.toggle_password_btn)

        form.addWidget(pass_lbl)
        form.addSpacing(6)
        form.addWidget(pass_row)
        form.addSpacing(24)

        # Sign In button
        self.login_button = QPushButton("Sign In")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setMinimumHeight(42)
        self.login_button.setStyleSheet(T.btn_primary())

        form.addWidget(self.login_button)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignLeft)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(
            f"QLabel {{ color: {T.DANGER}; background: {T.DANGER_BG}; "
            f"border: 1px solid #FECDD3; border-radius: {T.RADIUS_SM}; "
            f"padding: 10px 12px; font-size: 12px; margin-top: 10px; }}"
        )
        self.error_label.hide()
        form.addWidget(self.error_label)

        right_layout.addWidget(card, 0, Qt.AlignCenter)
        right_layout.addStretch()

        root.addWidget(left, 48)
        root.addWidget(right, 52)

        # Auth
        self.auth = AuthClient("AIzaSyAXG7m0qlHpg2bETH9bvSYnriYfnEQjzmI")
        self.login_button.clicked.connect(self.handle_login)
        self.email_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"QLabel {{ font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; "
            f"background: transparent; letter-spacing: 0.5px; text-transform: uppercase; }}"
        )
        return lbl

    def _toggle_password(self):
        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("Show")
            self.password_visible = False
        else:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("Hide")
            self.password_visible = True

    # ── First-login password change ───────────────────────────────────────────
    def show_password_change_dialog(self, user):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set New Password")
        dialog.setModal(True)
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(
            f"QDialog {{ background: {T.SURFACE}; }} "
            f"QLabel {{ background: transparent; }}"
        )

        layout = QVBoxLayout(dialog)
        layout.setSpacing(14)
        layout.setContentsMargins(36, 36, 36, 36)

        title = QLabel("Set a new password")
        title.setStyleSheet(
            f"QLabel {{ font-size: 17px; font-weight: 600; color: {T.TEXT}; }}"
        )
        layout.addWidget(title)

        msg = QLabel(
            f"Hi {user.get('username', 'there')} — "
            "please choose a new password before continuing."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; }}")
        layout.addWidget(msg)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        layout.addWidget(div)

        for lbl_text, attr, ph in [
            ("New password (min 6 characters)", "new_pass_input", "New password"),
            ("Confirm new password",            "confirm_pass_input", "Confirm password"),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(
                f"QLabel {{ font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; "
                f"letter-spacing: 0.4px; text-transform: uppercase; }}"
            )
            inp = QLineEdit()
            inp.setEchoMode(QLineEdit.Password)
            inp.setPlaceholderText(ph)
            inp.setStyleSheet(T.input_field())
            inp.setMinimumHeight(40)
            setattr(dialog, attr, inp)
            layout.addWidget(lbl)
            layout.addSpacing(4)
            layout.addWidget(inp)

        error_label = QLabel("")
        error_label.setStyleSheet(
            f"QLabel {{ color: {T.DANGER}; background: {T.DANGER_BG}; "
            f"border: 1px solid #FECDD3; border-radius: 5px; padding: 8px 10px; font-size: 12px; }}"
        )
        error_label.hide()
        layout.addWidget(error_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(T.btn_secondary())
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setMinimumHeight(40)
        change_btn = QPushButton("Change Password")
        change_btn.setStyleSheet(T.btn_primary())
        change_btn.setCursor(Qt.PointingHandCursor)
        change_btn.setMinimumHeight(40)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(change_btn)
        layout.addLayout(btn_row)

        def validate_and_accept():
            new_pass = dialog.new_pass_input.text().strip()
            confirm  = dialog.confirm_pass_input.text().strip()
            if not new_pass:
                error_label.setText("Password cannot be empty.")
                error_label.show(); return
            if len(new_pass) < 6:
                error_label.setText("Password must be at least 6 characters.")
                error_label.show(); return
            if new_pass != confirm:
                error_label.setText("Passwords do not match.")
                error_label.show(); return
            dialog.new_password = new_pass
            dialog.accept()

        change_btn.clicked.connect(validate_and_accept)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.new_pass_input.returnPressed.connect(validate_and_accept)
        dialog.confirm_pass_input.returnPressed.connect(validate_and_accept)
        dialog.new_password = None

        if dialog.exec() == QDialog.Accepted:
            return dialog.new_password
        return None

    # ── Login logic ───────────────────────────────────────────────────────────
    def handle_login(self):
        email    = self.email_input.text().strip()
        password = self.password_input.text()          # do NOT strip — passwords may contain spaces

        if not email or not password:
            self.error_label.setText("Email and password are required.")
            self.error_label.show()
            return

        self.login_button.setText("Signing in…")
        self.login_button.setEnabled(False)
        self.error_label.hide()

        try:
            # ── Step 1: authenticate with Firebase Auth ──────────────────────
            try:
                user_data = self.auth.sign_in(email, password)
            except Exception as auth_err:
                self.error_label.setText("Incorrect email or password. Please try again.")
                self.error_label.show()
                return

            # ── Step 2: load the user profile from the Realtime Database ─────
            from services.firebase_client import FirebaseClient
            fb = FirebaseClient()

            users        = fb.root.child("users").get() or {}
            current_user = None
            for uid, user in users.items():
                if user.get("email") == user_data["email"]:
                    current_user = user
                    break

            if not current_user:
                self.error_label.setText("User profile not found. Please contact your administrator.")
                self.error_label.show()
                return

            fb.record_login_time(current_user["user_id"])

            if current_user.get("first_login", False):
                new_password = self.show_password_change_dialog(current_user)
                if new_password:
                    try:
                        import firebase_admin
                        from firebase_admin import auth as firebase_auth
                        firebase_auth.update_user(current_user["user_id"], password=new_password)
                        current_user["first_login"] = False
                        fb.save_user(current_user)
                        from utils.modern_dialogs import ModernMessageBox
                        ModernMessageBox.success(
                            self, "Password Changed",
                            "Your password has been updated successfully."
                        )
                    except Exception as e:
                        from utils.modern_dialogs import ModernMessageBox
                        ModernMessageBox.error(self, "Error", f"Failed to update password: {str(e)}")
                        return
                else:
                    return

            self.login_success.emit(current_user)

        except Exception as e:
            self.error_label.setText(f"Login error: {str(e)}")
            self.error_label.show()
        finally:
            self.login_button.setText("Sign In")
            self.login_button.setEnabled(True)
