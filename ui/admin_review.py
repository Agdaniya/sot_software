from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QPushButton, QFrame, QListWidgetItem,
    QInputDialog, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QFont
from services.firebase_client import FirebaseClient
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox


ITEM_PROJECT = "project"
ITEM_DRAWING = "drawing"


# ── Custom widget: project header card ────────────────────────────────────────
class ProjectHeaderWidget(QWidget):
    def __init__(self, proj_name, client_name, n_pending, n_total, collapsed, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        has_pending = n_pending > 0
        accent      = "#f97316" if has_pending else "#10b981"   # orange / emerald
        accent_bg   = "#fff7ed" if has_pending else "#f0fdf4"
        badge_bg    = "#f97316" if has_pending else "#10b981"
        badge_txt   = f"  {n_pending} to review  " if has_pending else "  All reviewed  "

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(10)

        # Coloured left accent bar
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        outer.addWidget(bar)

        # Text block
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_lbl = QLabel(proj_name)
        name_lbl.setStyleSheet(
            f"font-size:13px; font-weight:700; color:#1e293b; background:transparent;"
        )
        text_col.addWidget(name_lbl)

        client_lbl = QLabel(client_name)
        client_lbl.setStyleSheet(
            "font-size:11px; color:#64748b; background:transparent;"
        )
        text_col.addWidget(client_lbl)
        outer.addLayout(text_col, 1)

        # Badge pill
        badge = QLabel(badge_txt)
        badge.setStyleSheet(
            f"background:{badge_bg}; color:white; font-size:10px; font-weight:700;"
            f"border-radius:10px; padding:3px 0px;"
        )
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(90)
        outer.addWidget(badge)

        # Drawing count chip
        count_lbl = QLabel(f"{n_total} dwg{'s' if n_total != 1 else ''}")
        count_lbl.setStyleSheet(
            "font-size:10px; color:#64748b; background:#f1f5f9;"
            "border-radius:8px; padding:3px 8px;"
        )
        outer.addWidget(count_lbl)

        # Chevron
        self.chevron = QLabel("▸" if collapsed else "▾")
        self.chevron.setStyleSheet(
            "font-size:14px; color:#94a3b8; background:transparent;"
        )
        outer.addWidget(self.chevron)

        self.setStyleSheet(f"""
            QWidget {{
                background: {accent_bg};
                border-radius: 10px;
            }}
        """)

    def set_collapsed(self, collapsed):
        self.chevron.setText("▸" if collapsed else "▾")


# ── Custom widget: drawing row card ──────────────────────────────────────────
class DrawingRowWidget(QWidget):
    def __init__(self, d_name, status, payment, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        submitted = (status == "submitted")

        if submitted:
            icon     = "⚡"
            status_txt = "Needs Review"
            status_bg  = "#fef3c7"
            status_fg  = "#92400e"
            left_col   = "#f59e0b"
        else:
            icon     = "✓"
            pay_suffix = "  · 💰 Paid" if payment else "  · 💸 Unpaid"
            status_txt = f"Client Approved{pay_suffix}"
            status_bg  = "#dcfce7"
            status_fg  = "#166534"
            left_col   = "#22c55e"

        outer = QHBoxLayout(self)
        outer.setContentsMargins(28, 8, 14, 8)   # extra left indent to show nesting
        outer.setSpacing(10)

        # Icon circle
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background:{left_col}22; color:{left_col}; border-radius:14px;"
            f"font-size:13px; font-weight:700;"
        )
        outer.addWidget(icon_lbl)

        # Name + status
        text_col = QVBoxLayout()
        text_col.setSpacing(1)

        name_lbl = QLabel(d_name)
        name_lbl.setStyleSheet(
            "font-size:12px; font-weight:600; color:#1e293b; background:transparent;"
        )
        text_col.addWidget(name_lbl)

        status_lbl = QLabel(status_txt)
        status_lbl.setStyleSheet(
            f"font-size:10px; color:{status_fg}; background:transparent;"
        )
        text_col.addWidget(status_lbl)
        outer.addLayout(text_col, 1)

        # Status chip
        chip = QLabel(f"  {'Review' if submitted else 'Approved'}  ")
        chip.setStyleSheet(
            f"background:{status_bg}; color:{status_fg}; font-size:10px;"
            f"font-weight:600; border-radius:8px; padding:3px 0px;"
        )
        chip.setFixedWidth(68)
        chip.setAlignment(Qt.AlignCenter)
        outer.addWidget(chip)

        self.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 8px;
                border-left: 3px solid #f1f5f9;
            }
        """)


# ── Main view ─────────────────────────────────────────────────────────────────
class AdminReview(QWidget):
    def __init__(self):
        super().__init__()
        self.fb = FirebaseClient()
        self.selected_project_id = None
        self.selected_drawing_id = None
        # All projects start collapsed — set to False to expand by default
        self._collapsed = {}
        self._DEFAULT_COLLAPSED = True

        import utils.theme as T
        self.setStyleSheet(T.app_base())

        # ── Layout: top sub-bar + two-panel body ──────────────────────────────
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

        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        root = QHBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── LEFT PANEL ──────────────────────────────────────────────────────
        left_frame = QFrame()
        left_frame.setFixedWidth(380)
        left_frame.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left = QVBoxLayout(left_frame)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(0)

        # Panel header
        left_hdr = QFrame()
        left_hdr.setFixedHeight(52)
        left_hdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        lh = QHBoxLayout(left_hdr)
        lh.setContentsMargins(16, 0, 16, 0)
        self.left_title = QLabel("Review & Payment")
        self.left_title.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent; }}"
        )
        self.pending_badge = QLabel()
        self.pending_badge.setStyleSheet(
            f"QLabel {{ background: {T.WARNING}; color: white; font-size: 10px; "
            f"font-weight: 700; border-radius: 10px; padding: 2px 8px; }}"
        )
        self.pending_badge.hide()
        lh.addWidget(self.left_title)
        lh.addSpacing(8)
        lh.addWidget(self.pending_badge)
        lh.addStretch()
        left.addWidget(left_hdr)

        # Legend strip
        legend_strip = QFrame()
        legend_strip.setFixedHeight(36)
        legend_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        ls = QHBoxLayout(legend_strip)
        ls.setContentsMargins(16, 0, 16, 0)
        ls.setSpacing(16)
        for colour, label in [(T.WARNING, "Needs Review"), (T.TEAL, "Approved")]:
            dot = QLabel()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {colour}; border-radius: 4px;")
            txt = QLabel(label)
            txt.setStyleSheet(f"font-size: 11px; color: {T.TEXT_SEC}; background: transparent;")
            pair = QHBoxLayout()
            pair.setSpacing(5)
            pair.setContentsMargins(0, 0, 0, 0)
            pair.addWidget(dot)
            pair.addWidget(txt)
            ls.addLayout(pair)
        ls.addStretch()
        left.addWidget(legend_strip)

        self.list = QListWidget()
        self.list.setStyleSheet(
            f"QListWidget {{ border: none; background: transparent; outline: none; }}"
            f"QListWidget::item {{ border-radius: 0; margin: 0; padding: 0; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: transparent; }}"
        )
        self.list.setSpacing(0)
        self.list.itemClicked.connect(self._on_item_clicked)
        left.addWidget(self.list)

        # ─── RIGHT PANEL ─────────────────────────────────────────────────────
        right_outer = QFrame()
        right_outer.setStyleSheet(
            f"QFrame {{ background: {T.BG}; border: none; }}"
        )

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {T.BG}; }}"
        )
        right_scroll.setWidget(right_outer)

        self.right = QVBoxLayout(right_outer)
        self.right.setContentsMargins(32, 28, 32, 28)
        self.right.setSpacing(16)

        self.empty_label = QLabel("← Select a drawing from the list to review it")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {T.TEXT_HINT}; font-size: 13px; background: transparent; padding: 60px 20px;"
        )
        self.right.addWidget(self.empty_label)
        self.right.addStretch()

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setSpacing(14)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_widget.hide()
        self.right.addWidget(self.details_widget)

        self.drawing_title = QLabel()
        self.drawing_title.setStyleSheet(
            f"font-size: 17px; font-weight: 600; color: {T.TEXT}; background: transparent; letter-spacing: -0.3px;"
        )

        self.project_name_label = QLabel()
        self.project_name_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {T.TEXT}; background: transparent;"
        )
        self.client_label = QLabel()
        self.client_label.setStyleSheet(
            f"font-size: 12px; color: {T.TEXT_SEC}; background: transparent;"
        )

        self.details_layout.addWidget(self.drawing_title)
        self.details_layout.addWidget(self.project_name_label)
        self.details_layout.addWidget(self.client_label)

        self.payment_status_label = QLabel()
        self.payment_status_label.setStyleSheet(
            f"font-size: 12px; padding: 6px 12px; border-radius: 4px; font-weight: 600;"
        )
        self.details_layout.addWidget(self.payment_status_label)

        substeps_title = QLabel("Sub-Steps")
        substeps_title.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {T.TEXT_SEC}; "
            f"background: transparent; letter-spacing: 0.5px; text-transform: uppercase;"
        )
        self.details_layout.addWidget(substeps_title)

        self.steps_container = QVBoxLayout()
        self.details_layout.addLayout(self.steps_container)

        self.payment_btn = QPushButton("Mark as Paid")
        self.payment_btn.setCheckable(True)
        self.payment_btn.setCursor(Qt.PointingHandCursor)
        self.payment_btn.setMinimumHeight(38)
        self.payment_btn.setStyleSheet(
            f"QPushButton {{ background: {T.SURFACE}; color: {T.WARNING}; "
            f"border: 1px solid #FED7AA; border-radius: {T.RADIUS_SM}; "
            f"padding: 0 18px; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #FFFBEB; }}"
            f"QPushButton:checked {{ background: {T.TEAL}; color: white; border: none; }}"
            f"QPushButton:checked:hover {{ background: #0D6460; }}"
        )
        self.payment_btn.clicked.connect(self.handle_payment_toggle)
        self.details_layout.addWidget(self.payment_btn)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)

        self.approve_btn = QPushButton("Approve & Mark Client Approved")
        self.approve_btn.setCursor(Qt.PointingHandCursor)
        self.approve_btn.setMinimumHeight(38)
        self.approve_btn.setStyleSheet(T.btn_success())
        self.approve_btn.clicked.connect(self.handle_approve)

        self.reject_btn = QPushButton("Reject")
        self.reject_btn.setCursor(Qt.PointingHandCursor)
        self.reject_btn.setMinimumHeight(38)
        self.reject_btn.setStyleSheet(T.btn_danger_filled())
        self.reject_btn.clicked.connect(self.handle_reject)

        btns_row.addWidget(self.approve_btn)
        btns_row.addWidget(self.reject_btn)
        self.details_layout.addLayout(btns_row)

        root.addWidget(left_frame)
        root.addWidget(right_scroll, 1)
        root_layout.addWidget(body, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)

        self.load_pending_reviews()

    # ── Click: drawings → detail panel; project headers → toggle ─────────────
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
        """Show/hide drawing rows and update chevron on project header widgets."""
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

    # ── Auto-refresh (preserves selection + collapse state) ───────────────────
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

    # ── Build grouped list ────────────────────────────────────────────────────
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

                relevant = []
                for drawing_id, drawing in proj_drawings.items():
                    status = drawing.get("status", "")
                    if status in ("submitted", "client_approved"):
                        relevant.append((drawing_id, drawing, status))

                if not relevant:
                    continue

                relevant.sort(key=lambda x: 0 if x[2] == "submitted" else 1)
                has_pending = any(d[2] == "submitted" for d in relevant)
                buckets.append((has_pending, project_id, project, relevant))

            buckets.sort(key=lambda x: (0 if x[0] else 1, x[2].get("name", "").lower()))

            total   = sum(len(b[3]) for b in buckets)
            pending = sum(sum(1 for d in b[3] if d[2] == "submitted") for b in buckets)

            self.left_title.setText("Review & Payment")
            if pending:
                self.pending_badge.setText(f"  {pending} pending  ")
                self.pending_badge.show()
            else:
                self.pending_badge.hide()

            for has_pending, project_id, project, drawing_list in buckets:
                # Preserve existing collapse state; new projects start collapsed
                collapsed = self._collapsed.get(project_id, self._DEFAULT_COLLAPSED)

                proj_name   = project.get("name", "Unknown Project")
                client_name = project.get("client_name", "")
                n_pending   = sum(1 for d in drawing_list if d[2] == "submitted")
                n_total     = len(drawing_list)

                # ── PROJECT HEADER ITEM ─────────────────────────────────
                # Gap spacer
                gap = QListWidgetItem()
                gap.setFlags(Qt.NoItemFlags)
                gap.setBackground(QColor("transparent"))
                gap.setSizeHint(QSize(0, 6))
                self.list.addItem(gap)

                proj_item = QListWidgetItem()
                proj_item.setData(Qt.UserRole,     project_id)
                proj_item.setData(Qt.UserRole + 1, ITEM_PROJECT)
                proj_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                proj_item.setSizeHint(QSize(0, 64))
                self.list.addItem(proj_item)

                # Attach the custom card widget
                header_w = ProjectHeaderWidget(
                    proj_name, client_name, n_pending, n_total, collapsed
                )
                self.list.setItemWidget(proj_item, header_w)

                # ── DRAWING ROW ITEMS ────────────────────────────────────
                for drawing_id, drawing, status in drawing_list:
                    d_item = QListWidgetItem()
                    d_item.setData(Qt.UserRole,     (project_id, drawing_id))
                    d_item.setData(Qt.UserRole + 1, ITEM_DRAWING)
                    d_item.setData(Qt.UserRole + 2, project_id)
                    d_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    d_item.setSizeHint(QSize(0, 52))
                    self.list.addItem(d_item)

                    payment = drawing.get("payment_received", False)
                    row_w = DrawingRowWidget(
                        drawing.get("name", "Unnamed"), status, payment
                    )
                    self.list.setItemWidget(d_item, row_w)

            self._apply_collapse()
            logger.info(f"Review list built: {pending} pending, {total} total")

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

            self.drawing_title.setText(drawing["name"])
            self.project_name_label.setText(f"📁  {project.get('name', '')}")
            self.client_label.setText(f"Client: {project.get('client_name', '')}")

            paid = drawing.get("payment_received", False)
            if paid:
                self.payment_status_label.setText("✅  PAID")
                self.payment_status_label.setStyleSheet("""
                    QLabel {
                        font-size:13px; padding:8px 14px; border-radius:6px;
                        font-weight:600; background:#d1fae5; color:#065f46;
                    }
                """)
            else:
                self.payment_status_label.setText("⚠️  UNPAID")
                self.payment_status_label.setStyleSheet("""
                    QLabel {
                        font-size:13px; padding:8px 14px; border-radius:6px;
                        font-weight:600; background:#fee2e2; color:#991b1b;
                    }
                """)

            self.payment_btn.blockSignals(True)
            self.payment_btn.setChecked(paid)
            self.payment_btn.setText("✅  Paid" if paid else "💰  Mark as Paid")
            self.payment_btn.blockSignals(False)

            while self.steps_container.count():
                it = self.steps_container.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()

            substeps = drawing.get("sub_steps", {})
            done     = [s for s in substeps.values() if s.get("completed", False)]
            pending  = [s for s in substeps.values() if not s.get("completed", False)]

            if substeps:
                sf = QFrame()
                sf.setStyleSheet("""
                    QFrame {
                        background: #f8fafc; border: 1px solid #e2e8f0;
                        border-radius: 8px;
                    }
                """)
                sfl = QVBoxLayout(sf)
                sfl.setContentsMargins(14, 12, 14, 12)
                sfl.setSpacing(6)

                for s in done:
                    l = QLabel(f"✓   {s.get('name', '')}")
                    l.setStyleSheet(
                        "QLabel{color:#16a34a;font-size:13px;"
                        "font-weight:600;background:transparent;}"
                    )
                    sfl.addWidget(l)
                for s in pending:
                    l = QLabel(f"○   {s.get('name', '')}")
                    l.setStyleSheet(
                        "QLabel{color:#94a3b8;font-size:13px;background:transparent;}"
                    )
                    sfl.addWidget(l)

                pct = int(len(done) / len(substeps) * 100)
                pl = QLabel(f"Progress: {len(done)}/{len(substeps)} steps  ({pct}%)")
                pl.setStyleSheet(
                    "QLabel{color:#64748b;font-size:12px;"
                    "background:transparent;margin-top:6px;}"
                )
                sfl.addWidget(pl)
                self.steps_container.addWidget(sf)
            else:
                l = QLabel("No sub-steps defined for this drawing")
                l.setStyleSheet(
                    "QLabel{color:#94a3b8;font-size:13px;"
                    "font-style:italic;background:transparent;}"
                )
                self.steps_container.addWidget(l)

            status  = drawing.get("status")
            can_act = (status == "submitted")
            self.approve_btn.setEnabled(can_act)
            self.reject_btn.setEnabled(can_act)

            logger.info(f"Details loaded for {self.selected_drawing_id}")

        except Exception as e:
            logger.error(f"Error loading details: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to load details: {e}")

    # ── Payment toggle ────────────────────────────────────────────────────────
    def handle_payment_toggle(self):
        if not self.selected_project_id or not self.selected_drawing_id:
            return
        try:
            is_paid = self.payment_btn.isChecked()
            self.fb.mark_drawing_paid(
                self.selected_project_id, self.selected_drawing_id, is_paid
            )
            self.payment_btn.setText("✅  Paid" if is_paid else "💰  Mark as Paid")
            logger.info(f"Payment for {self.selected_drawing_id}: {is_paid}")
            self.load_pending_reviews()
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item.data(Qt.UserRole + 1) != ITEM_DRAWING:
                    continue
                pid, did = item.data(Qt.UserRole)
                if pid == self.selected_project_id and did == self.selected_drawing_id:
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
            self, "Reject Drawing",
            "Provide a reason for rejection:", ""
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
                "result":   "rejected",
                "feedback": comment.strip()   # drawing_detail.py reads 'feedback'
            })
            logger.info(f"Rejected {self.selected_drawing_id}")
            self.load_pending_reviews()
            self.details_widget.hide()
            self.empty_label.show()
        except Exception as e:
            logger.error(f"Reject error: {e}")
            ModernMessageBox.error(self, "Error", f"Failed to reject: {e}")