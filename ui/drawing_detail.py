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
        header.setFixedHeight(56)
        header.setStyleSheet(T.topbar())
        hbl = QHBoxLayout(header)
        hbl.setContentsMargins(20, 0, 20, 0)
        hbl.setSpacing(0)

        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFixedHeight(30)
        back_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {T.TEXT_SEC}; "
            f"border: 1px solid {T.BORDER_SOLID}; border-radius: {T.RADIUS_SM}; "
            f"font-size: 12px; font-weight: 600; padding: 0 12px; }}"
            f"QPushButton:hover {{ background: {T.BG}; color: {T.TEXT}; }}"
        )
        back_btn.clicked.connect(self.go_back)

        sep_v = QFrame()
        sep_v.setFixedSize(1, 18)
        sep_v.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")

        drawing_name_lbl = QLabel(self.drawing["name"])
        drawing_name_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {T.TEXT};"
        )

        sep2 = QLabel("·")
        sep2.setStyleSheet(f"color: {T.TEXT_HINT}; margin: 0 8px;")

        proj_lbl = QLabel(f"{project['name']}  /  {project['client_name']}")
        proj_lbl.setStyleSheet(f"font-size: 12px; color: {T.TEXT_SEC};")

        status     = self.drawing["status"]
        status_txt = self._status_label(status)
        _status_meta = {
            "not_started":    ("#f3f4f6", "#6b7280"),
            "in_progress":    ("#fef9c3", "#92400e"),
            "submitted":      ("#ede9fe", "#5b21b6"),
            "admin_approved": ("#ccfbf1", "#0f766e"),
            "admin_rejected": ("#ffe4e6", "#be123c"),
            "client_approved":("#ccfbf1", "#0f766e"),
            "completed":      ("#ccfbf1", "#0f766e"),
        }
        pill_bg, pill_fg = _status_meta.get(status, (T.BG, T.TEXT_SEC))
        status_badge = QLabel(f"● {status_txt}")
        status_badge.setStyleSheet(
            f"background: {pill_bg}; color: {pill_fg}; border-radius: 10px; "
            f"padding: 4px 12px; font-size: 11px; font-weight: 600; "
            f"font-family: 'Courier New', monospace;"
        )

        hbl.addWidget(back_btn)
        hbl.addSpacing(12)
        hbl.addWidget(sep_v)
        hbl.addSpacing(12)
        hbl.addWidget(drawing_name_lbl)
        hbl.addWidget(sep2)
        hbl.addWidget(proj_lbl)
        hbl.addStretch()
        hbl.addWidget(status_badge)
        self._root_layout.addWidget(header)

        # ── Two-panel body ─────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left: scrollable drawing card
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {T.BG}; }}")

        left_content = QWidget()
        left_content.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        left_cl = QVBoxLayout(left_content)
        left_cl.setContentsMargins(28, 24, 28, 28)
        left_cl.setSpacing(16)

        left_card = QFrame()
        left_card.setStyleSheet(T.card())
        self.card_layout = QVBoxLayout(left_card)
        self.card_layout.setContentsMargins(24, 24, 24, 24)
        self.card_layout.setSpacing(16)
        self.build_card_content()

        left_cl.addWidget(left_card)
        left_cl.addStretch()
        left_scroll.setWidget(left_content)

        # ── RIGHT: notes panel ────────────────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-left: 1px solid {T.BORDER_SOLID}; }}"
        )
        right_card.setFixedWidth(340)
        notes_layout = QVBoxLayout(right_card)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(0)

        notes_hdr = QFrame()
        notes_hdr.setFixedHeight(52)
        notes_hdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        nh = QHBoxLayout(notes_hdr)
        nh.setContentsMargins(20, 0, 20, 0)
        notes_title = QLabel("Notes")
        notes_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        nh.addWidget(notes_title)
        notes_layout.addWidget(notes_hdr)

        notes_form = QFrame()
        notes_form.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        nf = QVBoxLayout(notes_form)
        nf.setContentsMargins(16, 14, 16, 14)
        nf.setSpacing(10)

        if self.current_user:
            self.note_input = QTextEdit()
            self.note_input.setPlaceholderText("Add a note…")
            self.note_input.setMaximumHeight(80)
            self.note_input.setStyleSheet(T.input_field_flat())
            nf.addWidget(self.note_input)

            add_note_btn = QPushButton("Add Note")
            add_note_btn.setCursor(Qt.PointingHandCursor)
            add_note_btn.setMinimumHeight(36)
            add_note_btn.setStyleSheet(T.btn_primary())
            add_note_btn.clicked.connect(self.add_note)
            nf.addWidget(add_note_btn)
        notes_layout.addWidget(notes_form)

        # Notes scroll area
        notes_scroll = QScrollArea()
        notes_scroll.setWidgetResizable(True)
        notes_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {T.BG}; }}")
        notes_container = QWidget()
        notes_container.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        self.notes_list_layout = QVBoxLayout(notes_container)
        self.notes_list_layout.setSpacing(10)
        self.notes_list_layout.setContentsMargins(16, 16, 16, 16)
        self.notes_list_layout.addStretch()
        notes_scroll.setWidget(notes_container)
        notes_layout.addWidget(notes_scroll, 1)

        self.load_notes()

        body_layout.addWidget(left_scroll, 1)
        body_layout.addWidget(right_card)
        self._root_layout.addWidget(body, 1)

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

            # Progress card
            prog_card = QFrame()
            prog_card.setStyleSheet(T.card())
            prog_card_layout = QVBoxLayout(prog_card)
            prog_card_layout.setContentsMargins(20, 16, 20, 16)
            prog_card_layout.setSpacing(10)

            prog_header = QHBoxLayout()
            prog_lbl = QLabel("PROGRESS")
            prog_lbl.setStyleSheet(
                f"font-size: 10px; font-weight: 600; color: {T.TEXT_HINT}; "
                f"letter-spacing: 1.5px;"
            )
            prog_count = QLabel(f"{completed}/{total} steps  ·  {pct}%")
            prog_count.setStyleSheet(
                f"font-size: 12px; color: {T.TEXT_SEC}; "
                f"font-family: 'Courier New', monospace;"
            )
            prog_header.addWidget(prog_lbl)
            prog_header.addStretch()
            prog_header.addWidget(prog_count)
            prog_card_layout.addLayout(prog_header)

            bar = QProgressBar()
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            fg_color = "#0f766e" if pct == 100 else T.ACCENT
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none; border-radius: 4px;
                    background: {T.BORDER};
                }}
                QProgressBar::chunk {{
                    background: {fg_color}; border-radius: 4px;
                }}
            """)
            prog_card_layout.addWidget(bar)
            self.card_layout.addWidget(prog_card)

        # ── Payment tracking (admin + approved states) ────────────────────────
        if self.is_admin and status in ["admin_approved", "client_approved"]:
            pay_frame = QFrame()
            pay_frame.setStyleSheet(T.card())
            pay_layout = QVBoxLayout(pay_frame)
            pay_layout.setContentsMargins(20, 16, 20, 16)
            pay_layout.setSpacing(6)

            pay_title = QLabel("PAYMENT")
            pay_title.setStyleSheet(
                f"font-size: 10px; font-weight: 600; color: {T.TEXT_HINT}; letter-spacing: 1.5px;"
            )
            pay_layout.addWidget(pay_title)

            self.payment_checkbox = QCheckBox("Payment received")
            self.payment_checkbox.setChecked(self.drawing.get("payment_received", False))
            self.payment_checkbox.setStyleSheet(f"""
                QCheckBox {{ font-size: 13px; color: {T.TEXT}; spacing: 8px; }}
                QCheckBox::indicator {{ width: 17px; height: 17px; border: 1.5px solid {T.BORDER_SOLID}; border-radius: 4px; background: {T.SURFACE}; }}
                QCheckBox::indicator:checked {{ background: {T.TEAL}; border-color: {T.TEAL}; }}
            """)
            self.payment_checkbox.stateChanged.connect(self.handle_payment_toggle)
            pay_layout.addWidget(self.payment_checkbox)

            payment_date = self.drawing.get("payment_date")
            if payment_date:
                try:
                    dt = datetime.fromisoformat(payment_date)
                    date_lbl = QLabel(f"Paid on {dt.strftime('%b %d, %Y at %I:%M %p')}")
                    date_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_HINT};")
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

        # ── Sub-steps card ────────────────────────────────────────────────────
        if sub_steps:
            steps_card = QFrame()
            steps_card.setStyleSheet(T.card())
            steps_card_layout = QVBoxLayout(steps_card)
            steps_card_layout.setContentsMargins(20, 16, 20, 16)
            steps_card_layout.setSpacing(12)

            steps_lbl = QLabel("DRAWING STEPS")
            steps_lbl.setStyleSheet(
                f"font-size: 10px; font-weight: 600; letter-spacing: 1.5px; "
                f"color: {T.TEXT_HINT};"
            )
            steps_card_layout.addWidget(steps_lbl)

            div = QFrame()
            div.setFixedHeight(1)
            div.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
            steps_card_layout.addWidget(div)

            self.step_list = QListWidget()
            self.step_list.setStyleSheet(
                f"QListWidget {{ border: none; background: transparent; outline: none; }}"
                f"QListWidget::item {{ padding: 10px 4px; border: none; "
                f"border-bottom: 1px solid {T.BORDER_SOLID}; "
                f"background: transparent; color: {T.TEXT}; font-size: 13px; }}"
                f"QListWidget::item:hover {{ background: {T.BG}; }}"
                f"QListWidget::indicator {{ width: 18px; height: 18px; border-radius: 4px; "
                f"border: 1.5px solid {T.BORDER_SOLID}; background: {T.SURFACE}; }}"
                f"QListWidget::indicator:checked {{ background: {T.TEAL}; border-color: {T.TEAL}; }}"
                f"QListWidget::indicator:unchecked:hover {{ border-color: {T.ACCENT}; }}"
            )

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

            steps_card_layout.addWidget(self.step_list)

            # ── Action button inside the steps card ───────────────────────────
            if not self.is_locked:
                btn_text = self._get_button_text()
                disabled = self._is_button_disabled()
                if btn_text:
                    sep2 = QFrame()
                    sep2.setFixedHeight(1)
                    sep2.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
                    steps_card_layout.addWidget(sep2)

                    adv_btn = QPushButton(btn_text)
                    adv_btn.setCursor(Qt.PointingHandCursor)
                    adv_btn.setMinimumHeight(42)
                    adv_btn.setEnabled(not disabled)
                    adv_btn.setStyleSheet(T.btn_primary())
                    adv_btn.clicked.connect(self.advance_status)
                    steps_card_layout.addWidget(adv_btn)

            self.card_layout.addWidget(steps_card)
        elif not self.is_locked:
            # No substeps — just show the action button
            btn_text = self._get_button_text()
            disabled = self._is_button_disabled()
            if btn_text:
                adv_btn = QPushButton(btn_text)
                adv_btn.setCursor(Qt.PointingHandCursor)
                adv_btn.setMinimumHeight(42)
                adv_btn.setEnabled(not disabled)
                adv_btn.setStyleSheet(T.btn_primary())
                adv_btn.clicked.connect(self.advance_status)
                self.card_layout.addWidget(adv_btn)

        self.card_layout.addStretch()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _status_label(self, status: str) -> str:
        mapping = {
            "not_started":    "Not Started",
            "in_progress":    "In Progress",
            "submitted":      "Submitted",
            "admin_approved": "Admin Approved",
            "admin_rejected": "Rejected",
            "client_approved":"Client Approved",
            "completed":      "Completed",
        }
        return mapping.get(status, status.replace("_", " ").title())

    def _get_button_text(self) -> str:
        sub_steps = self.drawing.get("sub_steps", {})
        total     = len(sub_steps)
        completed = sum(1 for s in sub_steps.values() if s.get("completed", False))
        remaining = total - completed
        if self.drawing["status"] == "in_progress" and remaining > 0:
            return f"Complete {remaining} remaining step{'s' if remaining != 1 else ''} first"
        transitions = {
            "not_started":    "Start Work",
            "in_progress":    "Complete & Submit for Review",
            "admin_rejected": "Resume & Resubmit",
        }
        return transitions.get(self.drawing["status"], "")

    def _is_button_disabled(self) -> bool:
        if self.drawing["status"] == "in_progress":
            sub_steps = self.drawing.get("sub_steps", {})
            total     = len(sub_steps)
            completed = sum(1 for s in sub_steps.values() if s.get("completed", False))
            return completed < total
        return False

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
                empty.setStyleSheet(f"color: {T.TEXT_HINT}; font-size: 12px; padding: 20px;")
                self.notes_list_layout.insertWidget(0, empty)
                return

            sorted_notes = sorted(notes.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            for note in sorted_notes:
                note_frame = QFrame()
                note_frame.setStyleSheet(
                    f"QFrame {{ background: {T.SURFACE}; border: none; "
                    f"border-radius: {T.RADIUS_SM}; }}"
                )
                nl = QVBoxLayout(note_frame)
                nl.setContentsMargins(14, 12, 14, 12)
                nl.setSpacing(4)

                meta_row = QHBoxLayout()
                author   = note.get("author_name", "Unknown")
                deleted  = note.get("author_deleted", False)
                author_lbl = QLabel(f"{author}{'  [deleted]' if deleted else ''}")
                author_lbl.setStyleSheet(
                    f"font-size: 12px; font-weight: 600; "
                    f"color: {'#DC2626' if deleted else T.TEXT};"
                )
                meta_row.addWidget(author_lbl)

                ts = note.get("created_at", "")
                try:
                    time_str = datetime.fromisoformat(ts).strftime("%b %d, %I:%M %p")
                except Exception:
                    time_str = ts
                time_lbl = QLabel(time_str)
                time_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_HINT};")
                meta_row.addStretch()
                meta_row.addWidget(time_lbl)
                nl.addLayout(meta_row)

                body_lbl = QLabel(note.get("content", ""))
                body_lbl.setWordWrap(True)
                body_lbl.setStyleSheet(f"font-size: 13px; color: {T.TEXT};")
                nl.addWidget(body_lbl)

                self.notes_list_layout.insertWidget(self.notes_list_layout.count() - 1, note_frame)
        except Exception as e:
            err = QLabel(f"Error loading notes: {str(e)}")
            err.setStyleSheet(f"color: {T.DANGER}; font-size: 12px;")
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
