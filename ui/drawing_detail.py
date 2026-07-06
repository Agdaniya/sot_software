from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton,
    QFrame, QProgressBar, QCheckBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from services.firebase_client import FirebaseClient
from utils.modern_dialogs import ModernMessageBox
from datetime import datetime
import utils.theme as T
import uuid


# Merged completed + submitted into one step.
VALID_TRANSITIONS = {
    "not_started":    ["in_progress"],
    "in_progress":    ["submitted"],
    "submitted":      [],
    "admin_rejected": ["in_progress"],
    "admin_approved": [],
    "client_approved":[]
}


class DrawingDetail(QWidget):
    def __init__(self, project_id, drawing_id, current_user=None):
        super().__init__()
        self.project_id   = project_id
        self.drawing_id   = drawing_id
        self.current_user = current_user
        self.fb           = FirebaseClient()

        self.setStyleSheet(T.app_base())

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setSpacing(0)
        self._root_layout.setContentsMargins(0, 0, 0, 0)

        self.load_drawing()

    # ── Full page rebuild ─────────────────────────────────────────────────────
    def load_drawing(self):
        self.drawing = (
            self.fb.root
            .child("drawings").child(self.project_id).child(self.drawing_id)
            .get()
        )
        self.is_locked = self.drawing["status"] == "client_approved"
        project        = self.fb.get_project(self.project_id)
        self.is_admin  = bool(
            self.current_user and
            self.current_user.get("role") in ["admin", "super_admin"]
        )

        # Clear layout
        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── Header bar ────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border: none;
                border-bottom: 1px solid {T.BORDER};
            }}
        """)
        hbl = QHBoxLayout(header)
        hbl.setContentsMargins(28, 0, 28, 0)
        hbl.setSpacing(14)

        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedHeight(32)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T.TEXT_SEC};
                border: 1px solid {T.BORDER}; border-radius: 5px;
                font-size: 12px; font-weight: 600; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {T.BG}; color: {T.TEXT}; }}
        """)
        back_btn.clicked.connect(self.go_back)

        drawing_name = QLabel(self.drawing["name"])
        drawing_name.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")

        sep = QLabel("·")
        sep.setStyleSheet(f"color: {T.TEXT_HINT}; background: transparent;")

        proj_lbl = QLabel(f"{project['name']}  /  {project['client_name']}")
        proj_lbl.setStyleSheet(f"font-size: 13px; color: {T.TEXT_SEC}; background: transparent;")

        # Status badge in header
        status     = self.drawing["status"]
        status_txt = self._status_label(status)
        fg, bg     = T.STATUS_COLORS.get(status, (T.TEXT_SEC, T.BG))
        status_badge = QLabel(status_txt)
        status_badge.setStyleSheet(f"""
            QLabel {{
                background: {bg}; color: {fg};
                border-radius: 4px; padding: 4px 12px;
                font-size: 11px; font-weight: 700;
            }}
        """)

        hbl.addWidget(back_btn)
        hbl.addSpacing(4)
        hbl.addWidget(drawing_name)
        hbl.addWidget(sep)
        hbl.addWidget(proj_lbl)
        hbl.addStretch()
        hbl.addWidget(status_badge)
        self._root_layout.addWidget(header)

        # ── Two-column scroll content ─────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {T.BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        cl = QHBoxLayout(content)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(20)

        # ── LEFT: drawing card ────────────────────────────────────────────────
        left_card = QFrame()
        left_card.setStyleSheet(T.card())
        left_card.setMinimumWidth(480)
        self.card_layout = QVBoxLayout(left_card)
        self.card_layout.setContentsMargins(28, 28, 28, 28)
        self.card_layout.setSpacing(20)
        self.build_card_content()

        # ── RIGHT: notes ──────────────────────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(T.card())
        right_card.setMinimumWidth(340)
        right_card.setMaximumWidth(460)
        notes_layout = QVBoxLayout(right_card)
        notes_layout.setContentsMargins(28, 28, 28, 28)
        notes_layout.setSpacing(14)

        notes_title = QLabel("Notes")
        notes_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {T.TEXT}; background: transparent;")
        notes_layout.addWidget(notes_title)

        if self.current_user:
            self.note_input = QTextEdit()
            self.note_input.setPlaceholderText("Add a note about this project…")
            self.note_input.setMaximumHeight(90)
            self.note_input.setStyleSheet(f"""
                QTextEdit {{
                    border: 1.5px solid {T.BORDER}; border-radius: {T.RADIUS_SM};
                    padding: 10px; font-size: 13px; background: {T.BG}; color: {T.TEXT};
                }}
                QTextEdit:focus {{ border-color: {T.ACCENT}; background: {T.SURFACE}; }}
            """)
            notes_layout.addWidget(self.note_input)

            add_note_btn = QPushButton("Add Note")
            add_note_btn.setCursor(Qt.PointingHandCursor)
            add_note_btn.setMinimumHeight(36)
            add_note_btn.setStyleSheet(T.btn_primary())
            add_note_btn.clicked.connect(self.add_note)
            notes_layout.addWidget(add_note_btn)

        # Notes scroll area
        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        notes_container = QWidget()
        notes_container.setStyleSheet(f"QWidget {{ background: transparent; }}")
        self.notes_list_layout = QVBoxLayout(notes_container)
        self.notes_list_layout.setSpacing(10)
        self.notes_list_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_list_layout.addStretch()
        notes_scroll.setWidget(notes_container)
        notes_layout.addWidget(notes_scroll)

        self.load_notes()

        cl.addWidget(left_card, 2)
        cl.addWidget(right_card, 1)
        scroll.setWidget(content)
        self._root_layout.addWidget(scroll)

    # ── Card content (rebuilds on state changes) ──────────────────────────────
    def build_card_content(self):
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        status    = self.drawing["status"]
        sub_steps = self.drawing.get("sub_steps", {})

        # ── Progress section ─────────────────────────────────────────────────
        if sub_steps:
            completed = sum(1 for s in sub_steps.values() if s.get("completed", False))
            total     = len(sub_steps)
            pct       = int((completed / total) * 100) if total else 0

            prog_header = QHBoxLayout()
            prog_lbl = QLabel("Progress")
            prog_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T.TEXT}; background: transparent;")
            prog_count = QLabel(f"{completed} / {total} steps")
            prog_count.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC}; background: transparent;")
            prog_header.addWidget(prog_lbl)
            prog_header.addStretch()
            prog_header.addWidget(prog_count)
            self.card_layout.addLayout(prog_header)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(True)
            bar.setFormat(f"{pct}%")
            bar.setFixedHeight(10)
            fg_color = T.SUCCESS if pct == 100 else T.ACCENT
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none; border-radius: 5px;
                    background: {T.BORDER}; text-align: center;
                    font-size: 10px; color: transparent;
                }}
                QProgressBar::chunk {{
                    background: {fg_color}; border-radius: 5px;
                }}
            """)
            self.card_layout.addWidget(bar)

        # ── Payment tracking (admin + approved states) ────────────────────────
        if self.is_admin and status in ["admin_approved", "client_approved"]:
            pay_frame = QFrame()
            pay_frame.setStyleSheet(f"""
                QFrame {{
                    background: {T.BG};
                    border: 1px solid {T.BORDER};
                    border-radius: {T.RADIUS_SM};
                }}
            """)
            pay_layout = QVBoxLayout(pay_frame)
            pay_layout.setContentsMargins(16, 14, 16, 14)
            pay_layout.setSpacing(6)

            pay_title = QLabel("Payment Tracking")
            pay_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent;")
            pay_layout.addWidget(pay_title)

            self.payment_checkbox = QCheckBox("Payment received")
            self.payment_checkbox.setChecked(self.drawing.get("payment_received", False))
            self.payment_checkbox.setStyleSheet(f"""
                QCheckBox {{ font-size: 13px; color: {T.TEXT}; background: transparent; spacing: 8px; }}
                QCheckBox::indicator {{ width: 17px; height: 17px; border: 1.5px solid {T.BORDER_MED}; border-radius: 4px; background: {T.SURFACE}; }}
                QCheckBox::indicator:checked {{ background: {T.SUCCESS}; border-color: {T.SUCCESS}; }}
            """)
            self.payment_checkbox.stateChanged.connect(self.handle_payment_toggle)
            pay_layout.addWidget(self.payment_checkbox)

            payment_date = self.drawing.get("payment_date")
            if payment_date:
                try:
                    dt = datetime.fromisoformat(payment_date)
                    date_lbl = QLabel(f"Paid on {dt.strftime('%b %d, %Y at %I:%M %p')}")
                    date_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_HINT}; background: transparent;")
                    pay_layout.addWidget(date_lbl)
                except Exception:
                    pass

            self.card_layout.addWidget(pay_frame)

        # ── Rejection feedback ────────────────────────────────────────────────
        if status == "admin_rejected":
            last_review = self.drawing.get("last_review", {})
            if last_review and not last_review.get("addressed", False):
                rej_frame = QFrame()
                rej_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {T.DANGER_BG};
                        border: 1px solid #FECACA;
                        border-radius: {T.RADIUS_SM};
                    }}
                """)
                rl = QVBoxLayout(rej_frame)
                rl.setContentsMargins(16, 14, 16, 14)
                rl.setSpacing(6)
                rej_title = QLabel("Rejection Feedback")
                rej_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {T.DANGER}; background: transparent;")
                rl.addWidget(rej_title)
                feedback = QLabel(last_review.get("feedback", "No feedback provided"))
                feedback.setWordWrap(True)
                feedback.setStyleSheet(f"font-size: 13px; color: #7F1D1D; background: transparent;")
                rl.addWidget(feedback)
                self.card_layout.addWidget(rej_frame)

        # ── Sub-steps ─────────────────────────────────────────────────────────
        if sub_steps:
            steps_lbl = QLabel("Drawing Steps")
            steps_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {T.TEXT}; background: transparent;")
            self.card_layout.addWidget(steps_lbl)

            self.step_list = QListWidget()
            self.step_list.setStyleSheet(f"""
                QListWidget {{
                    border: 1px solid {T.BORDER}; border-radius: {T.RADIUS_SM};
                    background: {T.BG}; outline: none; padding: 6px;
                }}
                QListWidget::item {{
                    padding: 10px 12px; border: none; border-radius: 5px;
                    margin-bottom: 3px; background: {T.SURFACE}; color: {T.TEXT};
                }}
                QListWidget::item:hover {{ background: {T.BG}; }}
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

        # ── Action button ─────────────────────────────────────────────────────
        if not self.is_locked:
            btn_text = self._get_button_text()
            if btn_text:
                adv_btn = QPushButton(btn_text)
                adv_btn.setCursor(Qt.PointingHandCursor)
                adv_btn.setMinimumHeight(42)
                adv_btn.setStyleSheet(T.btn_primary())
                adv_btn.clicked.connect(self.advance_status)
                self.card_layout.addWidget(adv_btn, 0, Qt.AlignRight)

        self.card_layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _status_label(self, status: str) -> str:
        mapping = {
            "not_started":    "Not Started",
            "in_progress":    "In Progress",
            "submitted":      "Submitted — Awaiting Review",
            "admin_approved": "Admin Approved",
            "admin_rejected": "Rejected — Needs Revision",
            "client_approved":"Client Approved",
        }
        return mapping.get(status, status.replace("_", " ").title())

    def _get_button_text(self) -> str:
        transitions = {
            "not_started":    "Start Work",
            "in_progress":    "Complete & Submit for Review",
            "admin_rejected": "Resume & Resubmit",
        }
        return transitions.get(self.drawing["status"], "")

    # ── Notes ─────────────────────────────────────────────────────────────────
    def load_notes(self):
        while self.notes_list_layout.count() > 1:
            item = self.notes_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            notes = self.fb.get_notes(self.project_id) or {}
            if not notes:
                empty = QLabel("No notes yet.")
                empty.setAlignment(Qt.AlignCenter)
                empty.setStyleSheet(f"color: {T.TEXT_HINT}; font-size: 12px; background: transparent; padding: 20px;")
                self.notes_list_layout.insertWidget(0, empty)
                return

            sorted_notes = sorted(notes.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            for note in sorted_notes:
                note_frame = QFrame()
                note_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {T.BG}; border: 1px solid {T.BORDER};
                        border-radius: {T.RADIUS_SM};
                    }}
                """)
                nl = QVBoxLayout(note_frame)
                nl.setContentsMargins(14, 12, 14, 12)
                nl.setSpacing(4)

                meta_row = QHBoxLayout()
                author   = note.get("author_name", "Unknown")
                deleted  = note.get("author_deleted", False)
                author_lbl = QLabel(f"{author}{'  [deleted]' if deleted else ''}")
                author_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {'#DC2626' if deleted else T.TEXT}; background: transparent;")
                meta_row.addWidget(author_lbl)

                ts = note.get("created_at", "")
                try:
                    time_str = datetime.fromisoformat(ts).strftime("%b %d, %I:%M %p")
                except Exception:
                    time_str = ts
                time_lbl = QLabel(time_str)
                time_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_HINT}; background: transparent;")
                meta_row.addStretch()
                meta_row.addWidget(time_lbl)
                nl.addLayout(meta_row)

                body = QLabel(note.get("content", ""))
                body.setWordWrap(True)
                body.setStyleSheet(f"font-size: 13px; color: {T.TEXT}; background: transparent; line-height: 1.4;")
                nl.addWidget(body)

                self.notes_list_layout.insertWidget(self.notes_list_layout.count() - 1, note_frame)
        except Exception as e:
            err = QLabel(f"Error loading notes: {str(e)}")
            err.setStyleSheet(f"color: {T.DANGER}; font-size: 12px; background: transparent;")
            self.notes_list_layout.insertWidget(0, err)

    def add_note(self):
        content = self.note_input.toPlainText().strip()
        if not content:
            ModernMessageBox.warning(self, "Empty Note", "Please enter some text before adding a note.")
            return
        try:
            note_id = str(uuid.uuid4())
            self.fb.add_note(self.project_id, note_id, {
                "note_id":    note_id,
                "author_id":  self.current_user.get("user_id", "unknown"),
                "author_name":self.current_user.get("username", "Unknown User"),
                "content":    content,
                "created_at": datetime.now().isoformat(),
            })
            self.note_input.clear()
            self.load_notes()
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to add note: {str(e)}")

    # ── Drawing actions ───────────────────────────────────────────────────────
    def handle_payment_toggle(self, state):
        if not self.is_admin:
            return
        try:
            is_paid = (state == Qt.Checked)
            self.fb.mark_drawing_paid(self.project_id, self.drawing_id, is_paid)
            self.drawing = (
                self.fb.root.child("drawings").child(self.project_id).child(self.drawing_id).get()
            )
            self.build_card_content()
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"Failed to update payment: {str(e)}")

    def update_substeps(self, item):
        if self.is_locked:
            return
        step_id   = item.data(Qt.UserRole)
        completed = item.checkState() == Qt.Checked
        self.fb.root.child("drawings").child(self.project_id).child(self.drawing_id) \
            .child("sub_steps").child(step_id).child("completed").set(completed)
        self.drawing = (
            self.fb.root.child("drawings").child(self.project_id).child(self.drawing_id).get()
        )
        self.build_card_content()

    def go_back(self):
        mw = self.window()
        if hasattr(mw, "go_back"):
            mw.go_back()

    def advance_status(self):
        current = self.drawing["status"]
        allowed = VALID_TRANSITIONS.get(current, [])
        if not allowed:
            ModernMessageBox.information(self, "No Further Actions", "This drawing has no further status changes.")
            return

        if current == "in_progress":
            sub_steps = self.drawing.get("sub_steps", {})
            if sub_steps and not all(s.get("completed", False) for s in sub_steps.values()):
                ModernMessageBox.warning(self, "Steps Incomplete",
                    "Please complete all sub-steps before submitting for review.")
                return

        next_status = allowed[0]
        ref = self.fb.root.child("drawings").child(self.project_id).child(self.drawing_id)

        if current == "admin_rejected" and next_status == "in_progress":
            ref.child("status").set(next_status)
            ref.child("last_review").child("addressed").set(True)
        else:
            ref.child("status").set(next_status)

        self.load_drawing()
