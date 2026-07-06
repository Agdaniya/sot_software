"""
Modern Dialog Utilities
Provides consistent, modern styling for all dialogs in the application
"""

from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt


class ModernMessageBox:
    """
    Modern styled message boxes that work in both light and dark modes
    Replaces standard QMessageBox with better UX
    """
    
    @staticmethod
    def _create_modern_dialog(parent, title, message, icon_emoji, buttons=None):
        """Create a modern styled dialog"""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        # Modern styling that works in both light and dark modes
        dialog.setStyleSheet("""
            QDialog {
                background: white;
            }
            QLabel {
                color: #1e293b;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Icon and title
        header_layout = QHBoxLayout()
        
        icon = QLabel(icon_emoji)
        icon.setStyleSheet("QLabel { font-size: 32px; }")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
            }
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #64748b;
                line-height: 1.6;
            }
        """)
        layout.addWidget(message_label)
        
        # Buttons
        if buttons:
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            for btn_text, btn_role, btn_color in buttons:
                btn = QPushButton(btn_text)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumWidth(100)
                
                if btn_role == "primary":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {btn_color};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 600;
                        }}
                        QPushButton:hover {{
                            opacity: 0.9;
                        }}
                        QPushButton:pressed {{
                            opacity: 0.8;
                        }}
                    """)
                    btn.clicked.connect(dialog.accept)
                else:  # secondary
                    btn.setStyleSheet("""
                        QPushButton {
                            background: transparent;
                            color: #64748b;
                            border: 2px solid #e2e8f0;
                            border-radius: 6px;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 600;
                        }
                        QPushButton:hover {
                            background: #f8fafc;
                            border-color: #cbd5e1;
                        }
                    """)
                    btn.clicked.connect(dialog.reject)
                
                button_layout.addWidget(btn)
            
            layout.addLayout(button_layout)
        
        return dialog
    
    @staticmethod
    def information(parent, title, message):
        """Show informational message (silent, no blocking)"""
        # For most operations, we'll just skip showing this
        # Only use for important completion messages
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            title,
            message,
            "ℹ️",
            [("OK", "primary", "#1e40af")]
        )
        dialog.exec()
    
    @staticmethod
    def success(parent, title, message):
        """Show success message"""
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            title,
            message,
            "✅",
            [("OK", "primary", "#16a34a")]
        )
        dialog.exec()
    
    @staticmethod
    def warning(parent, title, message):
        """Show warning message"""
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            title,
            message,
            "⚠️",
            [("OK", "primary", "#ea580c")]
        )
        dialog.exec()
    
    @staticmethod
    def error(parent, title, message):
        """Show error message"""
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            title,
            message,
            "❌",
            [("OK", "primary", "#dc2626")]
        )
        dialog.exec()
    
    @staticmethod
    def question(parent, title, message, yes_text="Yes", no_text="No"):
        """Show question dialog with yes/no"""
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            title,
            message,
            "❓",
            [
                (no_text, "secondary", "#64748b"),
                (yes_text, "primary", "#1e40af")
            ]
        )
        return dialog.exec() == QDialog.Accepted
    
    @staticmethod
    def confirm_delete(parent, item_name):
        """Show confirmation dialog for deletion"""
        dialog = ModernMessageBox._create_modern_dialog(
            parent,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone.",
            "🗑️",
            [
                ("Cancel", "secondary", "#64748b"),
                ("Delete", "primary", "#dc2626")
            ]
        )
        return dialog.exec() == QDialog.Accepted


def show_toast(parent, message, duration=2000, type="success"):
    """
    Show a non-blocking toast notification (optional enhancement)
    This is a placeholder for future implementation
    """
    pass