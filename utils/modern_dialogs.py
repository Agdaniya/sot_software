"""
Modern Dialog Utilities — SOT Design System
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt
import utils.theme as T


class ModernMessageBox:
    @staticmethod
    def _dialog(parent, title: str, message: str, accent: str, buttons=None) -> QDialog:
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"""
            QDialog {{ background: {T.SURFACE}; }}
            QLabel  {{ background: transparent; }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Title row with accent bar
        title_row = QHBoxLayout()
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"background: {accent}; border-radius: 2px; border: none;")
        title_row.addWidget(bar)
        title_row.addSpacing(10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {T.TEXT};")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {T.BORDER}; max-height: 1px;")
        layout.addWidget(div)

        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 13px; color: {T.TEXT_SEC}; line-height: 1.6;")
        layout.addWidget(msg_lbl)

        # Buttons
        if buttons:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(10)
            btn_row.addStretch()
            for btn_text, btn_role, btn_color in buttons:
                btn = QPushButton(btn_text)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(38)
                btn.setMinimumWidth(90)
                if btn_role == "primary":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {btn_color}; color: white; border: none;
                            border-radius: {T.RADIUS_SM}; padding: 0 20px;
                            font-size: 13px; font-weight: 600;
                        }}
                        QPushButton:hover {{ background: {btn_color}cc; }}
                    """)
                    btn.clicked.connect(dialog.accept)
                else:
                    btn.setStyleSheet(T.btn_secondary())
                    btn.clicked.connect(dialog.reject)
                btn_row.addWidget(btn)
            layout.addLayout(btn_row)

        return dialog

    @staticmethod
    def information(parent, title, message):
        d = ModernMessageBox._dialog(parent, title, message, T.ACCENT,
                                     [("OK", "primary", T.ACCENT)])
        d.exec()

    @staticmethod
    def success(parent, title, message):
        d = ModernMessageBox._dialog(parent, title, message, T.SUCCESS,
                                     [("OK", "primary", T.SUCCESS)])
        d.exec()

    @staticmethod
    def warning(parent, title, message):
        d = ModernMessageBox._dialog(parent, title, message, T.WARNING,
                                     [("OK", "primary", T.WARNING)])
        d.exec()

    @staticmethod
    def error(parent, title, message):
        d = ModernMessageBox._dialog(parent, title, message, T.DANGER,
                                     [("OK", "primary", T.DANGER)])
        d.exec()

    @staticmethod
    def question(parent, title, message, yes_text="Yes", no_text="No") -> bool:
        d = ModernMessageBox._dialog(parent, title, message, T.ACCENT, [
            (no_text,  "secondary", T.TEXT_SEC),
            (yes_text, "primary",   T.ACCENT),
        ])
        return d.exec() == QDialog.Accepted

    @staticmethod
    def confirm_delete(parent, item_name: str) -> bool:
        d = ModernMessageBox._dialog(
            parent,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone.",
            T.DANGER,
            [
                ("Cancel", "secondary", T.TEXT_SEC),
                ("Delete", "primary",   T.DANGER),
            ]
        )
        return d.exec() == QDialog.Accepted


def show_toast(parent, message, duration=2000, type="success"):
    """Placeholder for future toast notification."""
    pass
