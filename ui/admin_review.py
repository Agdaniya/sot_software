from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QPushButton, QFrame, QListWidgetItem,
    QInputDialog, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor
from services.firebase_client import FirebaseClient
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import utils.theme as T

ITEM_PROJECT = "project"
ITEM_DRAWING = "drawing"

# status → (label, dot_color, pill_bg, pill_fg)
STATUS_META = {
    "submitted":       ("Submitted",       "#6366f1", "#ede9fe", "#5b21b6"),
    "client_approved": ("Client Approved", "#0d9488", "#ccfbf1", "#0f766e"),
    "admin_approved":  ("Admin Approved",  "#0d9488", "#ccfbf1", "#0f766e"),
    "in_progress":     ("In Progress",     "#f59e0b", "#fef9c3", "#92400e"),
    "not_started":     ("Not Started",     "#9ca3af", "#f3f4f6", "#6b7280"),
    "admin_rejected":  ("Rejected",        "#ef4444", "#ffe4e6", "#be123c"),
    "rejected":        ("Rejected",        "#ef4444", "#ffe4e6", "#be123c"),
    "completed":       ("Completed",       "#0d9488", "#ccfbf1", "#0f766e"),
}
DEFAULT_STATUS_META = ("Unknown", "#9ca3af", "#f3f4f6", "#6b7280")


def status_meta(status):
    return STATUS_META.get(status, DEFAULT_STATUS_META)


def _display(text):
    if text and text == text.upper() and len(text) > 2:
        return text.title()
    return text


# ── Project header row ────────────────────────────────────────────────────────
class ProjectHeaderWidget(QWidget):
    def __init__(self, proj_name, client_name, n_pending, n_total, collapsed, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 12, 14, 12)
        outer.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        name_lbl = QLabel(_display(proj_name))
        name_lbl.setStyleSheet(
            f"font-size:15px; font-weight:800; color:{T.TEXT}; "
            f"background:transparent; border:none; letter-spacing:-0.2px;"
        )
        text_col.addWidget(name_lbl)

        sub = f"{_display(client_name)} · {n_total} drawing{'s' if n_total != 1 else ''}"
        client_lbl = QLabel(sub)
        client_lbl.setStyleSheet(
            f"font-size:12px; color:{T.TEXT_SEC}; background:transparent; border:none;"
        )
        text_col.addWidget(client_lbl)
        outer.addLayout(text_col, 1)

        if n_pending > 0:
            badge = QLabel(str(n_pending))
            badge.setFixedSize(22, 22)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "background:#f97316; color:white; font-size:11px; font-weight:700;"
                "border-radius:11px; border:none;"
            )
            outer.addWidget(badge)

        self.chevron = QLabel()
        self.chevron.setFixedWidth(18)
        self.chevron.setAlignment(Qt.AlignCenter)
        self.chevron.setStyleSheet(
            f"font-size:14px; color:{T.TEXT_SEC}; background:transparent; border:none;"
        )
        self.set_collapsed(collapsed)
        outer.addWidget(self.chevron)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")

    def set_collapsed(self, collapsed):
        self.chevron.setText("›" if collapsed else "⌄")


# ── Drawing row ───────────────────────────────────────────────────────────────
class DrawingRowWidget(QWidget):
    def __init__(self, d_name, status, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        label, dot_color, pill_bg, pill_fg = status_meta(status)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 9, 14, 9)
        outer.setSpacing(10)

        icon = QLabel("🗎")
        icon.setStyleSheet("font-size:13px; background:transparent; border:none; color:#94a3b8;")
        outer.addWidget(icon)

        name_lbl = QLabel(_display(d_name))
        name_lbl.setStyleSheet(
            f"font-size:13px; font-weight:500; color:{T.TEXT}; "
            f"background:transparent; border:none;"
        )
        outer.addWidget(name_lbl, 1)

        # pill with dot — monospace font to match design
        pill = QLabel()
        pill.setAlignment(Qt.AlignCenter)
        pill.setText(f"● {label}")
        pill.setStyleSheet(
            f"background:{pill_bg}; color:{pill_fg}; font-size:11px; font-weight:600;"
            f"font-family:'Courier New', 'Courier', monospace;"
            f"border-radius:10px; padding:3px 10px; border:none;"
        )
        outer.addWidget(pill)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")


# ── Main view ─────────────────────────────────────────────────────────────────
class AdminReview(QWidget):
    def __init__(self):
        super().__init__()
        self.fb = FirebaseClient()
        self.selected_project_id = None
        self.selected_drawing_id = None
        self._collapsed = {}
        self._DEFAULT_COLLAPSED = True

        self.setStyleSheet(T.app_base())

        from ui.admin_dashboard import make_topbar
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar, back_btn = make_topbar(
            self, None, None, show_back=True, back_title="Review & Payment"
        )
        if back_btn:
            back_btn.clicked.connect(self._go_back)
        root_layout.addWidget(topbar)

        # ── Summary bar (hidden — not shown in current design) ────────────────
        self.summary_bar = QFrame()
        self.summary_bar.setFixedHeight(44)
        self.summary_bar.hide()
        self.summary_bar.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        sb = QHBoxLayout(self.summary_bar)
        sb.setContentsMargins(24, 0, 24, 0)
        sb.setSpacing(24)

        self.summary_pending_lbl = QLabel()
        self.summary_pending_lbl.setStyleSheet(
            f"font-size:13px; font-weight:700; color:#b45309; "
            f"background:transparent; border:none;"
        )
        self.summary_total_lbl = QLabel()
        self.summary_total_lbl.setStyleSheet(
            f"font-size:13px; color:{T.TEXT_SEC}; "
            f"background:transparent; border:none;"
        )
        self.summary_approved_lbl = QLabel()
        self.summary_approved_lbl.setStyleSheet(
            f"font-size:13px; color:#0d9488; "
            f"background:transparent; border:none;"
        )
        sb.addWidget(self.summary_pending_lbl)
        sb.addWidget(self.summary_total_lbl)
        sb.addWidget(self.summary_approved_lbl)
        sb.addStretch()
        root_layout.addWidget(self.summary_bar)

        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        root = QHBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT PANEL ────────────────────────────────────────────────────────
        left_frame = QFrame()
        left_frame.setFixedWidth(360)
        left_frame.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left = QVBoxLayout(left_frame)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)

        # Header
        left_hdr = QFrame()
        left_hdr.setFixedHeight(56)
        left_hdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        lh = QHBoxLayout(left_hdr)
        lh.setContentsMargins(20, 0, 16, 0)
        lh.setSpacing(8)

        lh_title = QLabel("Drawings")
        lh_title.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{T.TEXT}; "
            f"background:transparent; border:none;"
        )
        lh.addWidget(lh_title)

        self.pending_badge = QLabel()
        self.pending_badge.setStyleSheet(
            "background:#fef3c7; color:#92400e; font-size:11px; font-weight:600;"
            "border-radius:10px; padding:2px 10px; border:none;"
        )
        self.pending_badge.hide()
        lh.addWidget(self.pending_badge)
        lh.addStretch()
        left.addWidget(left_hdr)

        # Legend strip
        legend_strip = QFrame()
        legend_strip.setFixedHeight(34)
        legend_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        ls = QHBoxLayout(legend_strip)
        ls.setContentsMargins(16, 0, 16, 0)
        ls.setSpacing(16)
        for colour, lbl_text in [("#f97316", "Needs Review"), ("#0d9488", "Approved")]:
            dot = QLabel("●")
            dot.setStyleSheet(
                f"color:{colour}; font-size:10px; background:transparent; border:none;"
            )
            txt = QLabel(lbl_text)
            txt.setStyleSheet(
                f"font-size:12px; color:{T.TEXT_SEC}; background:transparent; border:none;"
            )
            pair = QHBoxLayout()
            pair.setSpacing(4)
            pair.setContentsMargins(0, 0, 0, 0)
            pair.addWidget(dot)
            pair.addWidget(txt)
            ls.addLayout(pair)
        ls.addStretch()
        left.addWidget(legend_strip)

        # List
        self.list = QListWidget()
        self.list.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{ border: none; margin: 0; padding: 0; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: #f0f6ff; "
            f"border-left: 3px solid #3b82f6; }}"
        )
        self.list.setSpacing(0)
        self.list.itemClicked.connect(self._on_item_clicked)
        left.addWidget(self.list)

        # ── RIGHT PANEL ───────────────────────────────────────────────────────
        right_outer = QWidget()
        right_outer.setStyleSheet(f"QWidget {{ background: {T.BG}; border: none; }}")

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {T.BG}; }}"
        )
        right_scroll.setWidget(right_outer)

        self.right = QVBoxLayout(right_outer)
        self.right.setContentsMargins(28, 24, 28, 24)
        self.right.setSpacing(14)

        # Empty state
        self.empty_label = QLabel("← Select a drawing from the list to review it")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color:{T.TEXT_HINT}; font-size:13px; background:transparent; "
            f"border:none; padding:60px 20px;"
        )
        self.right.addWidget(self.empty_label)
        self.right.addStretch()

        # Details widget
        self.details_widget = QWidget()
        self.details_widget.setStyleSheet(
            "QWidget { background: transparent; border: none; }"
        )
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setSpacing(14)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_widget.hide()
        self.right.addWidget(self.details_widget)

        # ── Header: title + status chip ──
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(12)
        hdr_row.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title_col.setContentsMargins(0, 0, 0, 0)

        self.drawing_title = QLabel()
        self.drawing_title.setStyleSheet(
            f"font-size:20px; font-weight:700; color:{T.TEXT}; "
            f"background:transparent; border:none; letter-spacing:-0.3px;"
        )
        title_col.addWidget(self.drawing_title)

        self.subtitle_label = QLabel()
        self.subtitle_label.setStyleSheet(
            f"font-size:13px; color:{T.TEXT_HINT}; background:transparent; border:none;"
        )
        title_col.addWidget(self.subtitle_label)
        hdr_row.addLayout(title_col, 1)

        self.status_chip = QLabel()
        self.status_chip.setAlignment(Qt.AlignCenter)
        self.status_chip.setStyleSheet(
            "font-size:11px; font-weight:600; border-radius:10px; "
            "font-family:'Courier New', 'Courier', monospace;"
            "padding:5px 14px; border:none;"
        )
        hdr_row.addWidget(self.status_chip, 0, Qt.AlignTop)
        self.details_layout.addLayout(hdr_row)

        # ── Payment card ──
        payment_card = QFrame()
        payment_card.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: 10px; }}"
        )
        pcl = QVBoxLayout(payment_card)
        pcl.setContentsMargins(18, 14, 18, 14)
        pcl.setSpacing(10)

        pay_title = QLabel("PAYMENT")
        pay_title.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{T.TEXT_HINT}; "
            f"background:transparent; border:none; letter-spacing:1.5px;"
        )
        pcl.addWidget(pay_title)

        pay_row = QHBoxLayout()
        pay_row.setSpacing(10)
        pay_row.setContentsMargins(0, 0, 0, 0)

        self.payment_status_label = QLabel()
        self.payment_status_label.setAlignment(Qt.AlignCenter)
        self.payment_status_label.setStyleSheet(
            "font-size:12px; font-weight:700; padding:5px 12px; "
            "border-radius:6px; border:none;"
        )
        pay_row.addWidget(self.payment_status_label)

        self.payment_date_label = QLabel()
        self.payment_date_label.setStyleSheet(
            f"font-size:12px; color:{T.TEXT_SEC}; background:transparent; border:none;"
        )
        pay_row.addWidget(self.payment_date_label)
        pay_row.addStretch()

        self.payment_btn = QPushButton()
        self.payment_btn.setCursor(Qt.PointingHandCursor)
        self.payment_btn.setMinimumHeight(34)
        self.payment_btn.setStyleSheet(
            f"QPushButton {{ background: {T.SURFACE}; color: #0f766e; "
            f"border: 1.5px solid #0f766e; border-radius: 8px; "
            f"padding: 0 16px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #f0fdfa; border-color: #0d6460; color: #0d6460; }}"
        )
        self.payment_btn.clicked.connect(self.handle_payment_toggle)
        pay_row.addWidget(self.payment_btn)

        pcl.addLayout(pay_row)
        self.details_layout.addWidget(payment_card)

        # ── Steps card ──
        steps_card = QFrame()
        steps_card.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: 10px; }}"
        )
        scl = QVBoxLayout(steps_card)
        scl.setContentsMargins(18, 14, 18, 14)
        scl.setSpacing(10)

        self.steps_title = QLabel("STEPS")
        self.steps_title.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{T.TEXT_HINT}; "
            f"background:transparent; border:none; letter-spacing:1.5px;"
        )
        scl.addWidget(self.steps_title)

        self.steps_container = QVBoxLayout()
        self.steps_container.setSpacing(8)
        self.steps_container.setContentsMargins(0, 0, 0, 0)
        scl.addLayout(self.steps_container)
        self.details_layout.addWidget(steps_card)

        # ── Action buttons ──
        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)
        btns_row.setContentsMargins(0, 6, 0, 0)

        self.approve_btn = QPushButton("✓  Approve & Mark Client Approved")
        self.approve_btn.setCursor(Qt.PointingHandCursor)
        self.approve_btn.setMinimumHeight(42)
        self.approve_btn.setStyleSheet(
            f"QPushButton {{ background: #0f766e; color: white; border: none; "
            f"border-radius: 8px; font-size: 13px; font-weight: 700; padding: 0 20px; }}"
            f"QPushButton:hover {{ background: #0d6460; }}"
            f"QPushButton:disabled {{ background: {T.BORDER_SOLID}; color: {T.TEXT_HINT}; }}"
        )
        self.approve_btn.clicked.connect(self.handle_approve)

        self.reject_btn = QPushButton("✕  Reject")
        self.reject_btn.setCursor(Qt.PointingHandCursor)
        self.reject_btn.setMinimumHeight(42)
        self.reject_btn.setMinimumWidth(110)
        self.reject_btn.setStyleSheet(
            f"QPushButton {{ background: {T.SURFACE}; color: #dc2626; "
            f"border: 1.5px solid #fca5a5; border-radius: 8px; "
            f"font-size: 13px; font-weight: 700; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: #fef2f2; }}"
            f"QPushButton:disabled {{ color: {T.TEXT_HINT}; border-color: {T.BORDER_SOLID}; }}"
        )
        self.reject_btn.clicked.connect(self.handle_reject)

        btns_row.addWidget(self.approve_btn, 1)
        btns_row.addWidget(self.reject_btn)
        self.details_layout.addLayout(btns_row)

        root.addWidget(left_frame)
        root.addWidget(right_scroll, 1)
        root_layout.addWidget(body, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)

        self.load_pending_reviews()

    # ── Click handler ─────────────────────────────────────────────────────────
    def _on_item_clicked(self, item):
        kind = item.data(Qt.UserRole + 1)
        if kind == ITEM_DRAWING:
            self.load_drawing_details(item)
        elif kind == ITEM_PROJECT:
            project_id = item.data(Qt.UserRole)
            self._collapsed[project_id] = not self._collapsed.get(
                project_id, self._DEFAULT_COLLAPSED
            )
            self._apply_collapse()

    def _go_back(self):
        mw = self.window()
        if hasattr(mw, "go_back"):
            mw.go_back()

    def _apply_collapse(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            kind = item.data(Qt.UserRole + 1)
            if kind == ITEM_PROJECT:
                project_id = item.data(Qt.UserRole)
                collapsed  = self._collapsed.get(project_id, self._DEFAULT_COLLAPSED)
                w = self.list.itemWidget(item)
                if w:
                    w.set_collapsed(collapsed)
            elif kind == ITEM_DRAWING:
                pid = item.data(Qt.UserRole + 2)
                self.list.setRowHidden(
                    i, self._collapsed.get(pid, self._DEFAULT_COLLAPSED)
                )

    # ── Auto-refresh ──────────────────────────────────────────────────────────
    def auto_refresh(self):
        try:
            old_pid = self.selected_project_id
            old_did = self.selected_drawing_id
            self.load_pending_reviews()
            if old_pid and old_did:
                for i in range(self.list.count()):
                    item = self.list.item(i)
                    if item.data(Qt.UserRole + 1) != ITEM_DRAWING:
                        continue
                    pid, did = item.data(Qt.UserRole)
                    if pid == old_pid and did == old_did:
                        self.list.setCurrentItem(item)
                        self.load_drawing_details(item)
                        break
        except Exception:
            pass

    # ── Build list ────────────────────────────────────────────────────────────
    def load_pending_reviews(self):
        self.list.clear()
        try:
            all_projects = self.fb.root.child("projects").get() or {}
            all_drawings = self.fb.root.child("drawings").get() or {}

            buckets = []
            for project_id, project in all_projects.items():
                proj_drawings = all_drawings.get(project_id, {})
                if not isinstance(proj_drawings, dict):
                    continue
                relevant = [
                    (did, d, d.get("status", "not_started"))
                    for did, d in proj_drawings.items()
                ]
                if not relevant:
                    continue
                has_pending = any(s == "submitted" for _, _, s in relevant)
                buckets.append((has_pending, project_id, project, relevant))

            # pending projects first, then alpha
            buckets.sort(key=lambda x: (0 if x[0] else 1, x[2].get("name", "").lower()))

            total   = sum(len(b[3]) for b in buckets)
            pending = sum(sum(1 for _, _, s in b[3] if s == "submitted") for b in buckets)

            approved = sum(
                sum(1 for _, _, s in b[3] if s in ("client_approved", "admin_approved", "completed"))
                for b in buckets
            )

            # header badge
            if pending:
                self.pending_badge.setText(f"{pending} pending")
                self.pending_badge.show()
            else:
                self.pending_badge.hide()

            # summary bar
            self.summary_pending_lbl.setText(f"⏳  {pending} awaiting review")
            self.summary_total_lbl.setText(f"📋  {total} total drawings")
            self.summary_approved_lbl.setText(f"✓  {approved} approved")

            for has_pending, project_id, project, drawing_list in buckets:
                collapsed   = self._collapsed.get(project_id, self._DEFAULT_COLLAPSED)
                proj_name   = project.get("name", "Unknown")
                client_name = project.get("client_name", "")
                n_pending   = sum(1 for _, _, s in drawing_list if s == "submitted")
                n_total     = len(drawing_list)

                # small gap before each project
                gap = QListWidgetItem()
                gap.setFlags(Qt.NoItemFlags)
                gap.setSizeHint(QSize(0, 4))
                self.list.addItem(gap)

                proj_item = QListWidgetItem()
                proj_item.setData(Qt.UserRole, project_id)
                proj_item.setData(Qt.UserRole + 1, ITEM_PROJECT)
                proj_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                proj_item.setSizeHint(QSize(0, 62))
                self.list.addItem(proj_item)
                self.list.setItemWidget(
                    proj_item,
                    ProjectHeaderWidget(proj_name, client_name, n_pending, n_total, collapsed)
                )

                for drawing_id, drawing, status in drawing_list:
                    d_item = QListWidgetItem()
                    d_item.setData(Qt.UserRole, (project_id, drawing_id))
                    d_item.setData(Qt.UserRole + 1, ITEM_DRAWING)
                    d_item.setData(Qt.UserRole + 2, project_id)
                    d_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    d_item.setSizeHint(QSize(0, 44))
                    self.list.addItem(d_item)
                    self.list.setItemWidget(
                        d_item,
                        DrawingRowWidget(drawing.get("name", "Unnamed"), status)
                    )

            self._apply_collapse()
            logger.info(f"Review list: {pending} pending / {total} total")

        except Exception as e:
            logger.error(f"Error loading reviews: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to load reviews: {e}")

    # ── Detail panel ──────────────────────────────────────────────────────────
    def load_drawing_details(self, item):
        self.selected_project_id, self.selected_drawing_id = item.data(Qt.UserRole)
        try:
            drawing = self.fb.get_drawing(self.selected_project_id, self.selected_drawing_id)
            if not drawing:
                raise Exception("Drawing not found")
            project = self.fb.get_project(self.selected_project_id)
            if not project:
                raise Exception("Project not found")

            self.empty_label.hide()
            self.details_widget.show()

            self.drawing_title.setText(_display(drawing["name"]))
            self.subtitle_label.setText(
                f"{_display(project.get('name', ''))} · {_display(project.get('client_name', ''))}"
            )

            status = drawing.get("status", "not_started")
            label, dot_color, pill_bg, pill_fg = status_meta(status)
            self.status_chip.setText(f"● {label}")
            self.status_chip.setStyleSheet(
                f"background:{pill_bg}; color:{pill_fg}; font-size:11px; font-weight:600;"
                f"font-family:'Courier New', 'Courier', monospace;"
                f"border-radius:10px; padding:5px 14px; border:none;"
            )

            # payment
            paid = drawing.get("payment_received", False)
            if paid:
                self.payment_status_label.setText("PAID")
                self.payment_status_label.setStyleSheet(
                    "font-size:11px; font-weight:700; padding:4px 12px; "
                    "border-radius:6px; background:#d1fae5; color:#065f46; border:none; "
                    "font-family:'Courier New', 'Courier', monospace; letter-spacing:0.5px;"
                )
                paid_date = drawing.get("payment_date", "")
                if paid_date and len(paid_date) >= 10:
                    paid_date = paid_date[:10]
                self.payment_date_label.setText(paid_date)
                self.payment_date_label.setStyleSheet(
                    f"font-size:13px; color:{T.TEXT_SEC}; background:transparent; border:none;"
                )
                self.payment_date_label.setVisible(bool(paid_date))
                self.payment_btn.setText("Mark as Unpaid")
            else:
                self.payment_status_label.setText("UNPAID")
                self.payment_status_label.setStyleSheet(
                    "font-size:11px; font-weight:700; padding:4px 12px; "
                    "border-radius:6px; background:#f1f5f9; color:#64748b; border:none; "
                    "font-family:'Courier New', 'Courier', monospace; letter-spacing:0.5px;"
                )
                self.payment_date_label.setText("")
                self.payment_date_label.setVisible(False)
                self.payment_btn.setText("Mark as Paid")

            # steps
            while self.steps_container.count():
                it = self.steps_container.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()
                elif it.layout():
                    # clear nested layout
                    while it.layout().count():
                        c = it.layout().takeAt(0)
                        if c.widget():
                            c.widget().deleteLater()

            substeps = drawing.get("sub_steps", {})
            if substeps:
                done_steps    = [s for s in substeps.values() if s.get("completed", False)]
                pending_steps = [s for s in substeps.values() if not s.get("completed", False)]
                self.steps_title.setText(
                    f"STEPS — {len(done_steps)}/{len(substeps)}"
                )
                for s in done_steps:
                    self._add_step_row(s.get("name", ""), done=True)
                for s in pending_steps:
                    self._add_step_row(s.get("name", ""), done=False)
            else:
                self.steps_title.setText("STEPS")
                lbl = QLabel("No sub-steps defined for this drawing")
                lbl.setStyleSheet(
                    f"color:{T.TEXT_HINT}; font-size:13px; "
                    f"font-style:italic; background:transparent; border:none;"
                )
                self.steps_container.addWidget(lbl)

            can_act = (status == "submitted")
            self.approve_btn.setEnabled(can_act)
            self.reject_btn.setEnabled(can_act)

            logger.info(f"Details loaded: {self.selected_drawing_id}")

        except Exception as e:
            logger.error(f"Error loading details: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to load details: {e}")

    def _add_step_row(self, name, done):
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(0, 2, 0, 2)

        if done:
            dot = QLabel("✓")
            dot.setFixedSize(24, 24)
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet(
                "background:#0f766e; color:white; font-size:13px; font-weight:700;"
                "border-radius:12px; border:none;"
            )
            name_lbl = QLabel(_display(name))
            name_lbl.setStyleSheet(
                f"color:{T.TEXT}; font-size:14px; font-weight:400; "
                f"background:transparent; border:none;"
            )
        else:
            dot = QLabel()
            dot.setFixedSize(24, 24)
            dot.setStyleSheet(
                "background:transparent; border:2px solid #d1d5db; border-radius:12px;"
            )
            name_lbl = QLabel(_display(name))
            name_lbl.setStyleSheet(
                f"color:{T.TEXT_SEC}; font-size:14px; "
                f"background:transparent; border:none;"
            )

        row.addWidget(dot)
        row.addWidget(name_lbl, 1)

        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background: transparent; border: none; }")
        wrapper.setLayout(row)
        self.steps_container.addWidget(wrapper)

    # ── Payment toggle ────────────────────────────────────────────────────────
    def handle_payment_toggle(self):
        if not self.selected_project_id or not self.selected_drawing_id:
            return
        try:
            current = self.fb.get_drawing(self.selected_project_id, self.selected_drawing_id)
            is_paid = not current.get("payment_received", False)
            self.fb.mark_drawing_paid(self.selected_project_id, self.selected_drawing_id, is_paid)
            logger.info(f"Payment {self.selected_drawing_id}: {is_paid}")
            self.load_pending_reviews()
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item.data(Qt.UserRole + 1) != ITEM_DRAWING:
                    continue
                pid, did = item.data(Qt.UserRole)
                if pid == self.selected_project_id and did == self.selected_drawing_id:
                    self.list.setCurrentItem(item)
                    self.load_drawing_details(item)
                    break
        except Exception as e:
            logger.error(f"Payment error: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to update payment: {e}")

    # ── Approve ───────────────────────────────────────────────────────────────
    def handle_approve(self):
        if not self.selected_project_id or not self.selected_drawing_id:
            return
        try:
            self.fb.root.child("drawings") \
                .child(self.selected_project_id) \
                .child(self.selected_drawing_id) \
                .child("status").set("client_approved")
            logger.info(f"Approved → client_approved: {self.selected_drawing_id}")
            self.load_pending_reviews()
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item.data(Qt.UserRole + 1) != ITEM_DRAWING:
                    continue
                pid, did = item.data(Qt.UserRole)
                if pid == self.selected_project_id and did == self.selected_drawing_id:
                    self.list.setCurrentItem(item)
                    self.load_drawing_details(item)
                    break
        except Exception as e:
            logger.error(f"Approve error: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to approve: {e}")

    # ── Reject ────────────────────────────────────────────────────────────────
    def handle_reject(self):
        if not self.selected_project_id or not self.selected_drawing_id:
            return
        comment, ok = QInputDialog.getMultiLineText(
            self, "Reject Drawing", "Reason for rejection:", ""
        )
        if not ok:
            return
        if not comment.strip():
            ModernMessageBox.warning(self, "Required", "Please enter a rejection reason.")
            return
        try:
            ref = self.fb.root.child("drawings") \
                .child(self.selected_project_id) \
                .child(self.selected_drawing_id)
            ref.child("status").set("admin_rejected")
            ref.child("last_review").set({
                "result": "rejected",
                "feedback": comment.strip()
            })
            logger.info(f"Rejected {self.selected_drawing_id}")
            self.load_pending_reviews()
            self.details_widget.hide()
            self.empty_label.show()
        except Exception as e:
            logger.error(f"Reject error: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to reject: {e}")
