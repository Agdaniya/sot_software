from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem,
    QPushButton, QFrame, QProgressBar, QCheckBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from services.firebase_client import FirebaseClient
from utils.modern_dialogs import ModernMessageBox
from datetime import datetime
import uuid


# OPTIMISED: Merged completed + submitted into one step.
# Employees now click one button to complete all steps AND submit for review.
# Also merged admin_approved → client_approved is handled in AdminReview with one click.
VALID_TRANSITIONS = {
    "not_started": ["in_progress"],
    "in_progress": ["submitted"],       # MERGED: completing now immediately submits for review
    "submitted": [],                    # Admin will approve or reject
    "admin_rejected": ["in_progress"],  # Goes back to in_progress so employee can fix and resubmit
    "admin_approved": [],               # Admin review handles client approval directly
    "client_approved": []               # Final state
}


class DrawingDetail(QWidget):
    def __init__(self, project_id, drawing_id, current_user=None):
        super().__init__()
        self.project_id = project_id
        self.drawing_id = drawing_id
        self.current_user = current_user
        self.fb = FirebaseClient()

        self.setStyleSheet("""
            QWidget {
                background: #e8ebf0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
                color: #1e293b;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # PERFORMANCE FIX: Removed aggressive auto-refresh to prevent lag
        # Data will refresh on user actions instead of every 2 seconds

        self.load_drawing()

    def load_drawing(self):
        """Initial load of drawing - builds entire UI"""
        self.drawing = (
            self.fb.root
            .child("drawings")
            .child(self.project_id)
            .child(self.drawing_id)
            .get()
        )
        self.is_locked = self.drawing["status"] == "client_approved"

        # Get project info
        project = self.fb.get_project(self.project_id)

        # Check if user is admin
        self.is_admin = False
        if self.current_user:
            self.is_admin = self.current_user.get("role") in ["admin", "super_admin"]

        # Clear existing layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ================= HEADER =================
        header = QFrame()
        header.setFixedHeight(110)
        header.setStyleSheet("""
            QFrame {
                background: #1e40af;
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 20, 40, 20)
        header_layout.setSpacing(12)

        # Back button
        back_btn = QPushButton("←")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedSize(40, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
        back_btn.clicked.connect(self.go_back)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel(self.drawing['name'])
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 700;
                background: transparent;
            }
        """)

        subtitle = QLabel(f"{project['name']} - {project['client_name']}")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                background: transparent;
            }
        """)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addWidget(back_btn)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        self.layout.addWidget(header)

        # ================= CONTENT - TWO COLUMN LAYOUT =================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #e8ebf0;
            }
        """)
        
        content = QWidget()
        content_main_layout = QVBoxLayout(content)
        content_main_layout.setContentsMargins(40, 40, 40, 40)
        content_main_layout.setSpacing(24)

        # TWO COLUMN LAYOUT
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(24)

        # ================= LEFT COLUMN: DRAWING DETAILS =================
        left_column = QFrame()
        left_column.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        left_column.setMinimumWidth(500)

        self.card_layout = QVBoxLayout(left_column)
        self.card_layout.setContentsMargins(32, 32, 32, 32)
        self.card_layout.setSpacing(24)

        # Build dynamic content (status, steps, buttons, etc.)
        self.build_card_content()

        # ================= RIGHT COLUMN: NOTES =================
        right_column = QFrame()
        right_column.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        right_column.setMinimumWidth(400)
        right_column.setMaximumWidth(500)

        notes_layout = QVBoxLayout(right_column)
        notes_layout.setContentsMargins(32, 32, 32, 32)
        notes_layout.setSpacing(20)

        notes_title = QLabel("Project Notes 📝")
        notes_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        notes_layout.addWidget(notes_title)

        # Note input
        if self.current_user:
            self.note_input = QTextEdit()
            self.note_input.setPlaceholderText("Add a note about this project...")
            self.note_input.setMaximumHeight(100)
            self.note_input.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    background: #f8fafc;
                }
                QTextEdit:focus {
                    border: 2px solid #1e40af;
                    background: white;
                }
            """)
            notes_layout.addWidget(self.note_input)

            add_note_btn = QPushButton("Add Note")
            add_note_btn.setCursor(Qt.PointingHandCursor)
            add_note_btn.setStyleSheet("""
                QPushButton {
                    background: #1e40af;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #1e3a8a;
                }
            """)
            add_note_btn.clicked.connect(self.add_note)
            notes_layout.addWidget(add_note_btn)

        # Notes list (scrollable)
        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        notes_container = QWidget()
        self.notes_list_layout = QVBoxLayout(notes_container)
        self.notes_list_layout.setSpacing(12)
        self.notes_list_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_list_layout.addStretch()

        notes_scroll.setWidget(notes_container)
        notes_layout.addWidget(notes_scroll)

        # Load notes
        self.load_notes()

        # Add columns to layout
        columns_layout.addWidget(left_column, stretch=2)
        columns_layout.addWidget(right_column, stretch=1)

        content_main_layout.addLayout(columns_layout)

        scroll.setWidget(content)
        self.layout.addWidget(scroll)

    def build_card_content(self):
        """Build the dynamic content inside the main card (left column)"""
        # Clear existing content
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        # ===== DRAWING STATUS SECTION =====
        status_section = QVBoxLayout()
        status_section.setSpacing(12)

        status_header_layout = QHBoxLayout()
        status_label = QLabel("Drawing Status")
        status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)

        # Status badge
        status = self.drawing["status"]
        status_text = status.replace("_", " ").title()

        status_badge = QLabel(status_text)
        status_badge.setStyleSheet(f"""
            QLabel {{
                background: {self._get_status_color(status)};
                color: white;
                padding: 6px 16px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)

        status_header_layout.addWidget(status_label)
        status_header_layout.addStretch()
        status_header_layout.addWidget(status_badge)

        status_section.addLayout(status_header_layout)

        # Progress bar
        sub_steps = self.drawing.get("sub_steps", {})
        if sub_steps:
            completed = sum(1 for s in sub_steps.values() if s.get("completed", False))
            total = len(sub_steps)
            percentage = int((completed / total) * 100) if total > 0 else 0

            progress_text = QLabel(f"Progress: {completed}/{total} steps completed")
            progress_text.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    color: #64748b;
                    background: transparent;
                }
            """)
            status_section.addWidget(progress_text)

            progress_bar = QProgressBar()
            progress_bar.setValue(percentage)
            progress_bar.setTextVisible(True)
            progress_bar.setFormat(f"{percentage}%")
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 6px;
                    background: #e2e8f0;
                    height: 24px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background: #1e40af;
                    border-radius: 6px;
                }
            """)
            status_section.addWidget(progress_bar)

        self.card_layout.addLayout(status_section)

        # ===== ADMIN PAYMENT SECTION (if admin and approved) =====
        if self.is_admin and status in ["admin_approved", "client_approved"]:
            payment_frame = QFrame()
            payment_frame.setStyleSheet("""
                QFrame {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)

            payment_layout = QVBoxLayout(payment_frame)
            payment_layout.setSpacing(8)

            payment_title = QLabel("💰 Payment Tracking")
            payment_title.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    color: #1e293b;
                    background: transparent;
                }
            """)
            payment_layout.addWidget(payment_title)

            self.payment_checkbox = QCheckBox("Payment Received")
            self.payment_checkbox.setChecked(self.drawing.get("payment_received", False))
            self.payment_checkbox.stateChanged.connect(self.handle_payment_toggle)
            self.payment_checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #1e293b;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #cbd5e1;
                }
                QCheckBox::indicator:checked {
                    background: #16a34a;
                    border-color: #16a34a;
                }
            """)
            payment_layout.addWidget(self.payment_checkbox)

            payment_date = self.drawing.get("payment_date")
            if payment_date:
                try:
                    dt = datetime.fromisoformat(payment_date)
                    date_str = dt.strftime("%b %d, %Y at %I:%M %p")
                    date_label = QLabel(f"Paid on: {date_str}")
                    date_label.setStyleSheet("""
                        QLabel {
                            font-size: 12px;
                            color: #64748b;
                            background: transparent;
                        }
                    """)
                    payment_layout.addWidget(date_label)
                except:
                    pass

            self.card_layout.addWidget(payment_frame)

        # ===== REJECTION FEEDBACK =====
        if status == "admin_rejected":
            last_review = self.drawing.get("last_review", {})
            if last_review and not last_review.get("addressed", False):
                rejection_frame = QFrame()
                rejection_frame.setStyleSheet("""
                    QFrame {
                        background: #fee2e2;
                        border: 2px solid #dc2626;
                        border-radius: 8px;
                        padding: 16px;
                    }
                """)

                rejection_layout = QVBoxLayout(rejection_frame)
                rejection_layout.setSpacing(8)

                rejection_title = QLabel("❌ Admin Feedback")
                rejection_title.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        font-weight: 600;
                        color: #991b1b;
                        background: transparent;
                    }
                """)
                rejection_layout.addWidget(rejection_title)

                feedback = QLabel(last_review.get("feedback", "No feedback provided"))
                feedback.setWordWrap(True)
                feedback.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        color: #7f1d1d;
                        background: transparent;
                    }
                """)
                rejection_layout.addWidget(feedback)

                self.card_layout.addWidget(rejection_frame)

        # ===== DRAWING STEPS =====
        if sub_steps:
            steps_label = QLabel("Drawing Steps")
            steps_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: 600;
                    color: #1e293b;
                    background: transparent;
                    margin-top: 8px;
                }
            """)
            self.card_layout.addWidget(steps_label)

            self.step_list = QListWidget()
            self.step_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 8px;
                    background: #f8fafc;
                    outline: none;
                }
                QListWidget::item {
                    padding: 12px;
                    border: none;
                    border-radius: 6px;
                    margin-bottom: 4px;
                    background: white;
                }
                QListWidget::item:hover {
                    background: #f1f5f9;
                }
            """)

            for step_id, step in sub_steps.items():
                item = QListWidgetItem(step["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked if step.get("completed", False) else Qt.Unchecked)
                item.setData(Qt.UserRole, step_id)

                if self.is_locked:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

                self.step_list.addItem(item)

            if not self.is_locked:
                self.step_list.itemChanged.connect(self.update_substeps)

            self.card_layout.addWidget(self.step_list)

        # ===== ACTION BUTTONS =====
        if not self.is_locked:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(12)

            advance_btn = QPushButton(self._get_button_text())
            advance_btn.setCursor(Qt.PointingHandCursor)
            advance_btn.setStyleSheet("""
                QPushButton {
                    background: #1e40af;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background: #1e3a8a;
                }
                QPushButton:disabled {
                    background: #cbd5e1;
                    color: #94a3b8;
                }
            """)
            advance_btn.clicked.connect(self.advance_status)

            button_layout.addStretch()
            button_layout.addWidget(advance_btn)

            self.card_layout.addLayout(button_layout)

        self.card_layout.addStretch()

    def _get_status_color(self, status):
        """Get color for status badge"""
        colors = {
            "not_started": "#94a3b8",
            "in_progress": "#f59e0b",
            "completed": "#3b82f6",
            "submitted": "#6366f1",
            "admin_approved": "#16a34a",
            "admin_rejected": "#dc2626",
            "client_approved": "#10b981"
        }
        return colors.get(status, "#64748b")

    def _get_button_text(self):
        """Get appropriate button text based on current status"""
        current = self.drawing["status"]
        transitions = {
            "not_started": "▶ Start Work",
            "in_progress": "✓ Complete & Submit for Review",   # MERGED single step
            "admin_rejected": "▶ Resume & Resubmit"
        }
        return transitions.get(current, "Next Step")

    def load_notes(self):
        """Load and display notes"""
        # Clear existing notes
        while self.notes_list_layout.count() > 1:  # Keep the stretch at the end
            item = self.notes_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            notes = self.fb.get_notes(self.project_id) or {}
            
            if not notes:
                empty_label = QLabel("No notes yet. Be the first to add one!")
                empty_label.setStyleSheet("""
                    QLabel {
                        color: #94a3b8;
                        font-size: 13px;
                        font-style: italic;
                        background: transparent;
                        padding: 20px;
                    }
                """)
                empty_label.setAlignment(Qt.AlignCenter)
                self.notes_list_layout.insertWidget(0, empty_label)
                return
            
            # Sort notes by created_at (newest first)
            sorted_notes = sorted(
                notes.values(),
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            
            for note in sorted_notes:
                note_frame = QFrame()
                note_frame.setStyleSheet("""
                    QFrame {
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 12px;
                    }
                """)
                
                note_layout = QVBoxLayout(note_frame)
                note_layout.setSpacing(6)
                note_layout.setContentsMargins(0, 0, 0, 0)
                
                # Header with author and timestamp
                header_layout = QHBoxLayout()
                
                # FIX: Show indicator if author is deleted
                author_name = note.get('author_name', 'Unknown')
                is_deleted = note.get('author_deleted', False)

                if is_deleted:
                    author_display = f"{author_name} [DELETED USER]"
                    author_color = "#dc2626"  # Red color for deleted
                else:
                    author_display = author_name
                    author_color = "#1e293b"

                author_label = QLabel(author_display)
                author_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: 12px;
                        font-weight: 600;
                        color: {author_color};
                        background: transparent;
                    }}
                """)
                header_layout.addWidget(author_label)
                
                timestamp = note.get('created_at', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        time_str = dt.strftime("%b %d, %I:%M %p")
                    except:
                        time_str = timestamp
                else:
                    time_str = "Unknown time"
                
                time_label = QLabel(time_str)
                time_label.setStyleSheet("""
                    QLabel {
                        font-size: 11px;
                        color: #64748b;
                        background: transparent;
                    }
                """)
                header_layout.addWidget(time_label)
                header_layout.addStretch()
                
                note_layout.addLayout(header_layout)
                
                # Note content
                content_label = QLabel(note.get('content', ''))
                content_label.setWordWrap(True)
                content_label.setStyleSheet("""
                    QLabel {
                        font-size: 13px;
                        color: #1e293b;
                        background: transparent;
                        line-height: 1.4;
                    }
                """)
                note_layout.addWidget(content_label)
                
                self.notes_list_layout.insertWidget(self.notes_list_layout.count() - 1, note_frame)
                
        except Exception as e:
            error_label = QLabel(f"Error loading notes: {str(e)}")
            error_label.setStyleSheet("""
                QLabel {
                    color: #dc2626;
                    font-size: 12px;
                    background: transparent;
                }
            """)
            self.notes_list_layout.insertWidget(0, error_label)

    def add_note(self):
        """Add a new note to the project"""
        content = self.note_input.toPlainText().strip()
        
        if not content:
            ModernMessageBox.warning(
                self,
                "Empty Note",
                "Please enter some text for your note."
            )
            return
        
        try:
            note_id = str(uuid.uuid4())
            note_data = {
                "note_id": note_id,
                "author_id": self.current_user.get('user_id', 'unknown'),
                "author_name": self.current_user.get('username', 'Unknown User'),
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            self.fb.add_note(self.project_id, note_id, note_data)
            
            # Clear input
            self.note_input.clear()
            
            # Reload notes
            self.load_notes()
            
        except Exception as e:
            ModernMessageBox.error(
                self,
                "Error",
                f"Failed to add note: {str(e)}"
            )

    def handle_payment_toggle(self, state):
        """Handle payment checkbox toggle (admin only)"""
        if not self.is_admin:
            return
        
        try:
            is_paid = (state == Qt.Checked)
            self.fb.mark_drawing_paid(
                self.project_id,
                self.drawing_id,
                is_paid
            )
            
            # Reload drawing data and rebuild payment section
            self.drawing = self.fb.root.child("drawings") \
                .child(self.project_id) \
                .child(self.drawing_id) \
                .get()
            self.build_card_content()
            
        except Exception as e:
            ModernMessageBox.error(
                self,
                "Error",
                f"Failed to update payment status: {str(e)}"
            )

    def update_substeps(self, item):
        if self.is_locked:
            return

        step_id = item.data(Qt.UserRole)
        completed = item.checkState() == Qt.Checked

        self.fb.root.child("drawings") \
            .child(self.project_id) \
            .child(self.drawing_id) \
            .child("sub_steps") \
            .child(step_id) \
            .child("completed") \
            .set(completed)
        
        # Reload drawing data and rebuild to update progress
        self.drawing = self.fb.root.child("drawings") \
            .child(self.project_id) \
            .child(self.drawing_id) \
            .get()
        self.build_card_content()

    def go_back(self):
        """Go back to dashboard"""
        main_window = self.window()
        if hasattr(main_window, 'go_back'):
            main_window.go_back()

    def advance_status(self):
        """FIX: Advance to next status - STAY ON THIS PAGE"""
        current = self.drawing["status"]
        allowed = VALID_TRANSITIONS.get(current, [])

        if not allowed:
            ModernMessageBox.information(self, "Info", "No further status change allowed")
            return

        # Enforce sub-steps completion for in_progress -> submitted (MERGED step)
        if current == "in_progress":
            sub_steps = self.drawing.get("sub_steps", {})
            if sub_steps and not all(step.get("completed", False) for step in sub_steps.values()):
                ModernMessageBox.warning(
                    self,
                    "Incomplete Steps",
                    "Please complete all sub-steps before submitting for review."
                )
                return

        next_status = allowed[0]
        
        # FIX: Clear rejection feedback when resuming work
        if current == "admin_rejected" and next_status == "in_progress":
            drawing_ref = self.fb.root.child("drawings") \
                .child(self.project_id) \
                .child(self.drawing_id)
            
            drawing_ref.child("status").set(next_status)
            # Keep the review for reference but mark it as addressed
            drawing_ref.child("last_review").child("addressed").set(True)
        else:
            self.fb.root.child("drawings") \
                .child(self.project_id) \
                .child(self.drawing_id) \
                .child("status") \
                .set(next_status)

        # Reload entire page to show new status
        self.load_drawing()