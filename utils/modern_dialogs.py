"""
Modern Dialog Utilities — SOT Design System
Matches the React Modal / AlertModal component patterns.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
import utils.theme as T


class ModernMessageBox:

    @staticmethod
    def _dialog(parent, title: str, message: str, accent: str,
                buttons=None) -> QDialog:
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        dialog.setMaximumWidth(520)
        dialog.setStyleSheet(
            f"QDialog {{ background: {T.SURFACE}; border-radius: {T.RADIUS_LG}; }}"
            f"QLabel  {{ background: transparent; }}"
        )

        outer = QHBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left accent bar
        bar = QFrame()
        bar.setFixedWidth(5)
        bar.setStyleSheet(f"background: {accent}; border: none;")
        outer.addWidget(bar)

        inner = QVBoxLayout()
        inner.setContentsMargins(24, 24, 24, 24)
        inner.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"QLabel {{ font-size: 15px; font-weight: 600; color: {T.TEXT}; }}"
        )
        inner.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            f"QLabel {{ font-size: 13px; color: {T.TEXT_SEC}; line-height: 1.6; }}"
        )
        inner.addWidget(msg_lbl)

        if buttons:
            inner.addSpacing(8)
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)
            btn_row.addStretch()
            for btn_text, btn_role, btn_color in buttons:
                btn = QPushButton(btn_text)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(36)
                btn.setMinimumWidth(80)
                if btn_role == "primary":
                    btn.setStyleSheet(
                        f"QPushButton {{ background: {btn_color}; color: white; border: none; "
                        f"border-radius: {T.RADIUS_SM}; padding: 0 18px; "
                        f"font-size: 13px; font-weight: 600; }}"
                        f"QPushButton:hover {{ background: {btn_color}CC; }}"
                    )
                    btn.clicked.connect(dialog.accept)
                else:
                    btn.setStyleSheet(T.btn_secondary())
                    btn.clicked.connect(dialog.reject)
                btn_row.addWidget(btn)
            inner.addLayout(btn_row)

        outer.addLayout(inner)
        return dialog

    @staticmethod
    def information(parent, title, message):
        d = ModernMessageBox._dialog(
            parent, title, message, T.ACCENT,
            [("OK", "primary", T.ACCENT)]
        )
        d.exec()

    @staticmethod
    def success(parent, title, message):
        d = ModernMessageBox._dialog(
            parent, title, message, T.TEAL,
            [("OK", "primary", T.TEAL)]
        )
        d.exec()

    @staticmethod
    def warning(parent, title, message):
        d = ModernMessageBox._dialog(
            parent, title, message, T.WARNING,
            [("OK", "primary", T.WARNING)]
        )
        d.exec()

    @staticmethod
    def error(parent, title, message):
        d = ModernMessageBox._dialog(
            parent, title, message, T.DANGER,
            [("OK", "primary", T.DANGER)]
        )
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
