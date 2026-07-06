# Admin Template — restyled to match SOT design system (flush three-column layout)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QListWidget, QLineEdit, QPushButton, QFrame,
    QListWidgetItem, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt
from services.firebase_client import FirebaseClient
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
from ui.admin_dashboard import make_topbar
import utils.theme as T
import uuid


class AdminTemplate(QWidget):
    def __init__(self, user=None, on_back=None, on_logout=None):
        super().__init__()
        self.fb = FirebaseClient()
        self.selected_drawing_id = None
        self._user = user or {}
        self._on_back = on_back
        self._on_logout = on_logout

        # ── Root layout (full-screen column) ──────────────────────────────────
        root_v = QVBoxLayout(self)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar, back_btn = make_topbar(
            self, self._user,
            on_logout=self._on_logout,
            show_back=True,
            back_title="Project Template Manager"
        )
        if back_btn and self._on_back:
            back_btn.clicked.connect(self._on_back)
        root_v.addWidget(topbar)

        # ── Three-column body ─────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # ── COL 1 : Template Drawings (fixed 280px) ───────────────────────────
        col1 = QFrame()
        col1.setFixedWidth(280)
        col1.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        v1 = QVBoxLayout(col1)
        v1.setContentsMargins(0, 0, 0, 0)
        v1.setSpacing(0)

        # Header strip
        hdr1 = QFrame()
        hdr1.setFixedHeight(44)
        hdr1.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        hdr1_h = QHBoxLayout(hdr1)
        hdr1_h.setContentsMargins(16, 0, 16, 0)
        lbl1 = QLabel("Template Drawings")
        lbl1.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; "
            f"color: {T.TEXT}; background: transparent; }}"
        )
        tip1 = QLabel("Drag to reorder")
        tip1.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: {T.TEXT_SEC}; background: transparent; }}"
        )
        hdr1_h.addWidget(lbl1)
        hdr1_h.addStretch()
        hdr1_h.addWidget(tip1)
        v1.addWidget(hdr1)

        # Drawing list
        self.drawings = QListWidget()
        self.drawings.setDragDropMode(QListWidget.InternalMove)
        self.drawings.setDefaultDropAction(Qt.MoveAction)
        self.drawings.setStyleSheet(
            f"QListWidget {{ border: none; background: transparent; outline: none; }}"
            f"QListWidget::item {{"
            f"  padding: 10px 16px; background: {T.SURFACE}; color: {T.TEXT};"
            f"  border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{"
            f"  background: {T.ACCENT_BG}; color: {T.TEXT};"
            f"  border-left: 2px solid {T.ACCENT}; }}"
        )
        self.drawings.itemClicked.connect(self.load_substeps)
        self.drawings.model().rowsMoved.connect(self.save_drawing_order)
        v1.addWidget(self.drawings, 1)

        # Add-drawing input strip at bottom of col 1
        add1_strip = QFrame()
        add1_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-top: 1px solid {T.BORDER_SOLID}; }}"
        )
        add1_h = QHBoxLayout(add1_strip)
        add1_h.setContentsMargins(10, 8, 10, 8)
        add1_h.setSpacing(6)

        self.new_draw = QLineEdit()
        self.new_draw.setPlaceholderText("New drawing name…")
        self.new_draw.setFixedHeight(32)
        self.new_draw.setStyleSheet(T.input_field_flat())

        add_draw_btn = QPushButton("Add")
        add_draw_btn.setFixedHeight(32)
        add_draw_btn.setCursor(Qt.PointingHandCursor)
        add_draw_btn.setStyleSheet(T.btn_primary())
        add_draw_btn.clicked.connect(self.add_drawing)
        self.new_draw.returnPressed.connect(add_draw_btn.click)

        add1_h.addWidget(self.new_draw, 1)
        add1_h.addWidget(add_draw_btn)
        v1.addWidget(add1_strip)

        # Delete-drawing button strip
        del1_strip = QFrame()
        del1_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-top: 1px solid {T.BORDER_SOLID}; }}"
        )
        del1_h = QHBoxLayout(del1_strip)
        del1_h.setContentsMargins(10, 8, 10, 8)

        del_draw_btn = QPushButton("Delete Selected Drawing")
        del_draw_btn.setFixedHeight(32)
        del_draw_btn.setCursor(Qt.PointingHandCursor)
        del_draw_btn.setStyleSheet(T.btn_danger())
        del_draw_btn.clicked.connect(self.delete_drawing)
        del1_h.addWidget(del_draw_btn)
        v1.addWidget(del1_strip)

        # ── COL 2 : Sub-Steps list (stretch) ──────────────────────────────────
        col2 = QFrame()
        col2.setStyleSheet(
            f"QFrame {{ background: {T.BG}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        v2 = QVBoxLayout(col2)
        v2.setContentsMargins(0, 0, 0, 0)
        v2.setSpacing(0)

        # Header strip (title updates when drawing selected)
        hdr2 = QFrame()
        hdr2.setFixedHeight(44)
        hdr2.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        hdr2_h = QHBoxLayout(hdr2)
        hdr2_h.setContentsMargins(16, 0, 16, 0)
        self.col2_title = QLabel("Sub-Steps")
        self.col2_title.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; "
            f"color: {T.TEXT}; background: transparent; }}"
        )
        hdr2_h.addWidget(self.col2_title)
        hdr2_h.addStretch()
        v2.addWidget(hdr2)

        # Stacked widget: empty placeholder vs actual list
        self.substep_stack = QStackedWidget()
        self.substep_stack.setStyleSheet("background: transparent; border: none;")

        # Page 0 — empty state
        empty_page = QWidget()
        empty_page.setStyleSheet(f"background: {T.BG};")
        ep_v = QVBoxLayout(empty_page)
        ep_v.setAlignment(Qt.AlignCenter)
        self.empty_substeps = QLabel("← Select a drawing to view its sub-steps")
        self.empty_substeps.setAlignment(Qt.AlignCenter)
        self.empty_substeps.setStyleSheet(
            f"QLabel {{ color: {T.TEXT_SEC}; font-size: 13px; "
            f"font-style: italic; background: transparent; padding: 40px 20px; }}"
        )
        ep_v.addWidget(self.empty_substeps)
        self.substep_stack.addWidget(empty_page)        # index 0

        # Page 1 — substep list
        list_page = QWidget()
        list_page.setStyleSheet(f"background: {T.BG};")
        lp_v = QVBoxLayout(list_page)
        lp_v.setContentsMargins(0, 0, 0, 0)
        lp_v.setSpacing(0)

        self.substeps = QListWidget()
        self.substeps.setDragDropMode(QListWidget.InternalMove)
        self.substeps.setDefaultDropAction(Qt.MoveAction)
        self.substeps.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{"
            f"  padding: 10px 16px; background: {T.SURFACE}; color: {T.TEXT};"
            f"  border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{"
            f"  background: {T.ACCENT_BG}; color: {T.TEXT};"
            f"  border-left: 2px solid {T.ACCENT}; }}"
        )
        self.substeps.model().rowsMoved.connect(self.save_substep_order)
        lp_v.addWidget(self.substeps, 1)
        self.substep_stack.addWidget(list_page)         # index 1

        v2.addWidget(self.substep_stack, 1)

        # Add-substep input strip at bottom of col 2
        add2_strip = QFrame()
        add2_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-top: 1px solid {T.BORDER_SOLID}; }}"
        )
        add2_h = QHBoxLayout(add2_strip)
        add2_h.setContentsMargins(10, 8, 10, 8)
        add2_h.setSpacing(6)

        self.substep_name = QLineEdit()
        self.substep_name.setPlaceholderText("New sub-step name…")
        self.substep_name.setFixedHeight(32)
        self.substep_name.setStyleSheet(T.input_field_flat())

        self.add_substep_btn = QPushButton("Add")
        self.add_substep_btn.setFixedHeight(32)
        self.add_substep_btn.setCursor(Qt.PointingHandCursor)
        self.add_substep_btn.setEnabled(False)
        self.add_substep_btn.setStyleSheet(T.btn_primary())
        self.add_substep_btn.clicked.connect(self.add_substep)
        self.substep_name.returnPressed.connect(self.add_substep_btn.click)

        add2_h.addWidget(self.substep_name, 1)
        add2_h.addWidget(self.add_substep_btn)
        v2.addWidget(add2_strip)

        # Delete-substep button strip
        del2_strip = QFrame()
        del2_strip.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-top: 1px solid {T.BORDER_SOLID}; }}"
        )
        del2_h = QHBoxLayout(del2_strip)
        del2_h.setContentsMargins(10, 8, 10, 8)

        del_step_btn = QPushButton("Delete Selected Sub-Step")
        del_step_btn.setFixedHeight(32)
        del_step_btn.setCursor(Qt.PointingHandCursor)
        del_step_btn.setStyleSheet(T.btn_danger())
        del_step_btn.clicked.connect(self.delete_substep)
        del2_h.addWidget(del_step_btn)
        v2.addWidget(del2_strip)

        # ── COL 3 : Info panel (fixed 240px) ──────────────────────────────────
        col3 = QFrame()
        col3.setFixedWidth(240)
        col3.setStyleSheet(f"QFrame {{ background: {T.BG}; border: none; }}")
        v3 = QVBoxLayout(col3)
        v3.setContentsMargins(0, 0, 0, 0)
        v3.setSpacing(0)

        hdr3 = QFrame()
        hdr3.setFixedHeight(44)
        hdr3.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        hdr3_h = QHBoxLayout(hdr3)
        hdr3_h.setContentsMargins(16, 0, 16, 0)
        lbl3 = QLabel("Info")
        lbl3.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; "
            f"color: {T.TEXT}; background: transparent; }}"
        )
        hdr3_h.addWidget(lbl3)
        v3.addWidget(hdr3)

        info_body = QFrame()
        info_body.setStyleSheet(f"QFrame {{ background: {T.BG}; border: none; }}")
        info_v = QVBoxLayout(info_body)
        info_v.setContentsMargins(16, 16, 16, 16)
        info_v.setSpacing(12)
        info_v.setAlignment(Qt.AlignTop)

        # Selected drawing card
        sel_card = QFrame()
        sel_card.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: 1px solid {T.BORDER_SOLID}; "
            f"border-radius: {T.RADIUS}; }}"
        )
        sel_v = QVBoxLayout(sel_card)
        sel_v.setContentsMargins(12, 10, 12, 10)
        sel_v.setSpacing(4)
        sel_card_label = QLabel("SELECTED DRAWING")
        sel_card_label.setStyleSheet(
            f"QLabel {{ font-size: 9px; font-weight: 700; letter-spacing: 0.8px; "
            f"color: {T.TEXT_SEC}; background: transparent; }}"
        )
        self.drawing_display = QLabel("(None selected)")
        self.drawing_display.setWordWrap(True)
        self.drawing_display.setStyleSheet(
            f"QLabel {{ font-size: 13px; font-weight: 600; "
            f"color: {T.TEXT}; background: transparent; }}"
        )
        self.substep_count_lbl = QLabel("")
        self.substep_count_lbl.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: {T.TEXT_HINT}; background: transparent; }}"
        )
        sel_v.addWidget(sel_card_label)
        sel_v.addWidget(self.drawing_display)
        sel_v.addWidget(self.substep_count_lbl)
        info_v.addWidget(sel_card)

        # Propagation notice card
        notice_card = QFrame()
        notice_card.setStyleSheet(
            f"QFrame {{ background: #FFFBEB; border: 1px solid #FDE68A; "
            f"border-radius: {T.RADIUS}; }}"
        )
        notice_v = QVBoxLayout(notice_card)
        notice_v.setContentsMargins(12, 10, 12, 10)
        notice_v.setSpacing(4)
        notice_title = QLabel("Template Propagation")
        notice_title.setStyleSheet(
            f"QLabel {{ font-size: 12px; font-weight: 700; "
            f"color: #92400E; background: transparent; }}"
        )
        notice_body = QLabel(
            "Changes apply to all new projects. "
            "Existing projects are not affected retroactively."
        )
        notice_body.setWordWrap(True)
        notice_body.setStyleSheet(
            f"QLabel {{ font-size: 11px; color: #78350F; background: transparent; "
            f"line-height: 1.5; }}"
        )
        notice_v.addWidget(notice_title)
        notice_v.addWidget(notice_body)
        info_v.addWidget(notice_card)

        info_v.addStretch()
        v3.addWidget(info_body, 1)

        # ── Assemble columns into body ─────────────────────────────────────────
        body.addWidget(col1)
        body.addWidget(col2, 1)
        body.addWidget(col3)

        root_v.addLayout(body, 1)

        # ── Load data ─────────────────────────────────────────────────────────
        self.load_template()

    # ── Business logic (unchanged) ────────────────────────────────────────────

    def sync_template_to_projects(self, change_type, drawing_id=None, drawing_data=None, step_id=None, step_data=None):
        """
        Sync template changes to all existing projects.

        change_type options:
          'add_drawing'    - add a new drawing to every project
          'delete_drawing' - remove a drawing from every project
          'add_substep'    - add a new substep to a drawing in every project
          'delete_substep' - remove a substep from a drawing in every project
        """
        try:
            all_projects = self.fb.get_all_projects()
            updated = 0

            for project_id in all_projects.keys():
                try:
                    if change_type == 'add_drawing' and drawing_id and drawing_data:
                        existing = self.fb.get_drawing(project_id, drawing_id)
                        if not existing:
                            sub_steps = {}
                            for sid, step in drawing_data.get('sub_steps', {}).items():
                                sub_steps[sid] = {"name": step["name"], "completed": False, "order": step.get("order", 0)}
                            self.fb.save_drawing(project_id, drawing_id, {
                                "name": drawing_data["name"],
                                "status": "not_started",
                                "sub_steps": sub_steps,
                                "payment_received": False,
                                "payment_date": None
                            })
                            updated += 1

                    elif change_type == 'delete_drawing' and drawing_id:
                        existing = self.fb.get_drawing(project_id, drawing_id)
                        if existing and existing.get("status") == "not_started":
                            self.fb.root.child("drawings").child(project_id).child(drawing_id).delete()
                            updated += 1

                    elif change_type == 'add_substep' and drawing_id and step_id and step_data:
                        existing_drawing = self.fb.get_drawing(project_id, drawing_id)
                        if existing_drawing:
                            self.fb.root.child("drawings").child(project_id).child(drawing_id) \
                                .child("sub_steps").child(step_id).set({
                                    "name": step_data["name"],
                                    "completed": False,
                                    "order": step_data.get("order", 0)
                                })
                            updated += 1

                    elif change_type == 'delete_substep' and drawing_id and step_id:
                        existing_drawing = self.fb.get_drawing(project_id, drawing_id)
                        if existing_drawing:
                            sub_steps = existing_drawing.get("sub_steps", {})
                            if step_id in sub_steps and not sub_steps[step_id].get("completed", False):
                                self.fb.root.child("drawings").child(project_id).child(drawing_id) \
                                    .child("sub_steps").child(step_id).delete()
                                updated += 1

                except Exception as proj_err:
                    logger.warning(f"Could not sync to project {project_id}: {proj_err}")

            logger.info(f"Template sync '{change_type}': updated {updated}/{len(all_projects)} projects")

        except Exception as e:
            logger.error(f"Template sync failed for '{change_type}': {e}")

    def load_template(self):
        """Load all drawings from template, sorted by order."""
        self.drawings.clear()
        try:
            template = self.fb.get_project_template()
            drawings_list = []
            for drawing_id, drawing in template.items():
                order = drawing.get('order', 999)
                drawings_list.append((order, drawing_id, drawing))
            drawings_list.sort(key=lambda x: x[0])

            for order, drawing_id, drawing in drawings_list:
                substeps_count = len(drawing.get('sub_steps', {}))
                display_text = f"{drawing['name']}\n{substeps_count} sub-step{'s' if substeps_count != 1 else ''}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, drawing_id)
                self.drawings.addItem(item)

            logger.info(f"Loaded {len(template)} drawings")
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")

    def save_drawing_order(self):
        """Save new drawing order after drag-and-drop."""
        try:
            template = self.fb.get_project_template()
            for index in range(self.drawings.count()):
                item = self.drawings.item(index)
                drawing_id = item.data(Qt.UserRole)
                if drawing_id in template:
                    template[drawing_id]['order'] = index
            for drawing_id, drawing in template.items():
                self.fb.save_template_drawing(drawing_id, drawing)
            logger.info("Saved new drawing order")
        except Exception as e:
            logger.error(f"Error saving drawing order: {str(e)}")

    def save_substep_order(self):
        """Save new substep order after drag-and-drop."""
        if not self.selected_drawing_id:
            return
        try:
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps = drawing.get('sub_steps', {})
            for index in range(self.substeps.count()):
                item = self.substeps.item(index)
                step_id = item.data(Qt.UserRole)
                if step_id in substeps:
                    substeps[step_id]['order'] = index
            drawing['sub_steps'] = substeps
            self.fb.save_template_drawing(self.selected_drawing_id, drawing)
            logger.info(f"Saved new substep order for drawing: {self.selected_drawing_id}")
        except Exception as e:
            logger.error(f"Error saving substep order: {str(e)}")

    def load_substeps(self, item):
        """Load sub-steps for selected drawing."""
        drawing_id = item.data(Qt.UserRole)
        self.selected_drawing_id = drawing_id
        try:
            template = self.fb.get_project_template()
            drawing = template.get(drawing_id, {})

            drawing_name = drawing.get('name', 'Unknown')
            self.drawing_display.setText(drawing_name)
            self.col2_title.setText(f'Sub-Steps — "{drawing_name}"')

            self.substeps.clear()

            substeps = drawing.get('sub_steps', {})
            substeps_list = []
            for step_id, step in substeps.items():
                order = step.get('order', 999)
                substeps_list.append((order, step_id, step))
            substeps_list.sort(key=lambda x: x[0])

            for order, step_id, step in substeps_list:
                step_item = QListWidgetItem(step['name'])
                step_item.setData(Qt.UserRole, step_id)
                self.substeps.addItem(step_item)

            count = len(substeps)
            self.substep_count_lbl.setText(f"{count} sub-step{'s' if count != 1 else ''}")
            self.substep_stack.setCurrentIndex(1)
            self.add_substep_btn.setEnabled(True)

            logger.info(f"Loaded {count} sub-steps for drawing: {drawing_id}")
        except Exception as e:
            logger.error(f"Error loading sub-steps: {str(e)}")

    def update_drawing_substep_count(self):
        """Update only the substep count for the current drawing without full reload."""
        if not self.selected_drawing_id:
            return
        try:
            current_row = self.drawings.currentRow()
            if current_row < 0:
                return
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps_count = len(drawing.get('sub_steps', {}))
            current_item = self.drawings.item(current_row)
            display_text = f"{drawing['name']}\n{substeps_count} sub-step{'s' if substeps_count != 1 else ''}"
            current_item.setText(display_text)
            self.substep_count_lbl.setText(
                f"{substeps_count} sub-step{'s' if substeps_count != 1 else ''}"
            )
            logger.info(f"Updated substep count for drawing: {self.selected_drawing_id}")
        except Exception as e:
            logger.error(f"Error updating substep count: {str(e)}")

    def add_drawing(self):
        """Add a new drawing to the template."""
        name = self.new_draw.text().strip()
        if not name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a drawing name")
            return
        try:
            drawing_id = str(uuid.uuid4())
            template = self.fb.get_project_template()
            max_order = max([d.get('order', 0) for d in template.values()], default=-1)
            drawing_data = {"name": name, "sub_steps": {}, "order": max_order + 1}
            self.fb.save_template_drawing(drawing_id, drawing_data)
            logger.info(f"Added drawing: {drawing_id}")
            self.new_draw.clear()
            display_text = f"{name}\n0 sub-steps"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, drawing_id)
            self.drawings.addItem(item)
            self.drawings.setCurrentItem(item)
            self.sync_template_to_projects('add_drawing', drawing_id=drawing_id, drawing_data=drawing_data)
        except Exception as e:
            logger.error(f"Error adding drawing: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to add drawing: {str(e)}")

    def delete_drawing(self):
        """Delete selected drawing from template."""
        selected = self.drawings.currentItem()
        if not selected:
            ModernMessageBox.warning(self, "No Selection", "Please select a drawing to delete")
            return
        drawing_id = selected.data(Qt.UserRole)
        drawing_name = selected.text().split('\n')[0]
        if ModernMessageBox.confirm_delete(self, drawing_name):
            try:
                self.fb.delete_template_drawing(drawing_id)
                logger.info(f"Deleted drawing: {drawing_id}")
                self.sync_template_to_projects('delete_drawing', drawing_id=drawing_id)
                self.selected_drawing_id = None
                self.drawing_display.setText("(None selected)")
                self.substep_count_lbl.setText("")
                self.col2_title.setText("Sub-Steps")
                self.substep_stack.setCurrentIndex(0)
                self.add_substep_btn.setEnabled(False)
                self.load_template()
            except Exception as e:
                logger.error(f"Error deleting drawing: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to delete drawing: {str(e)}")

    def add_substep(self):
        """Add a new sub-step and immediately show it without full reload."""
        if not self.selected_drawing_id:
            ModernMessageBox.warning(self, "No Drawing Selected", "Please select a drawing first")
            return
        name = self.substep_name.text().strip()
        if not name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a sub-step name")
            return
        try:
            step_id = str(uuid.uuid4())
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps = drawing.get('sub_steps', {})
            max_order = max([s.get('order', 0) for s in substeps.values()], default=-1)
            step_data = {"name": name, "completed": False, "order": max_order + 1}
            self.fb.add_template_substep(self.selected_drawing_id, step_id, step_data)
            logger.info(f"Added sub-step: {step_id}")
            self.substep_name.clear()
            step_item = QListWidgetItem(name)
            step_item.setData(Qt.UserRole, step_id)
            self.substeps.addItem(step_item)
            self.update_drawing_substep_count()
            self.sync_template_to_projects('add_substep', drawing_id=self.selected_drawing_id,
                                           step_id=step_id, step_data=step_data)
        except Exception as e:
            logger.error(f"Error adding sub-step: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to add sub-step: {str(e)}")

    def delete_substep(self):
        """Delete selected sub-step without full reload."""
        if not self.selected_drawing_id:
            ModernMessageBox.warning(self, "No Drawing Selected", "Please select a drawing first")
            return
        selected = self.substeps.currentItem()
        if not selected:
            ModernMessageBox.warning(self, "No Selection", "Please select a sub-step to delete")
            return
        step_id = selected.data(Qt.UserRole)
        step_name = selected.text()
        if ModernMessageBox.confirm_delete(self, step_name):
            try:
                self.fb.delete_template_substep(self.selected_drawing_id, step_id)
                logger.info(f"Deleted sub-step: {step_id}")
                row = self.substeps.row(selected)
                self.substeps.takeItem(row)
                self.update_drawing_substep_count()
                self.sync_template_to_projects('delete_substep', drawing_id=self.selected_drawing_id,
                                               step_id=step_id)
            except Exception as e:
                logger.error(f"Error deleting sub-step: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to delete sub-step: {str(e)}")
