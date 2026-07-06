# Admin Template - Now with DRAG & DROP REORDERING and improved highlighting
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QLineEdit, QPushButton, QFrame, QListWidgetItem
)
from PySide6.QtCore import Qt
from services.firebase_client import FirebaseClient
from utils.logger import logger
from utils.modern_dialogs import ModernMessageBox
import uuid


class AdminTemplate(QWidget):
    def __init__(self):
        super().__init__()
        self.fb = FirebaseClient()
        self.selected_drawing_id = None

        self.setStyleSheet("""
            QWidget {
                background: #e8ebf0;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
                color: #1e293b;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        # ===== LEFT: DRAWINGS =====
        left_frame = QFrame()
        left_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        
        left = QVBoxLayout(left_frame)
        left.setContentsMargins(32, 32, 32, 32)
        left.setSpacing(16)
        
        left_title = QLabel("Template Drawings")
        left_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        left.addWidget(left_title)

        # FIX #4: Enable drag and drop for reordering
        self.drawings = QListWidget()
        self.drawings.setDragDropMode(QListWidget.InternalMove)
        self.drawings.setDefaultDropAction(Qt.MoveAction)
        self.drawings.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 0;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 20px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 12px;
                background: #f8fafc;
                color: #1e293b;
            }
            QListWidget::item:hover {
                background: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            QListWidget::item:selected {
                background: white;
                border: 2px solid #1e40af;
                color: #1e293b;
            }
        """)
        self.drawings.itemClicked.connect(self.load_substeps)
        # FIX #4: Connect to save new order when items are moved
        self.drawings.model().rowsMoved.connect(self.save_drawing_order)
        left.addWidget(self.drawings)

        # Reordering help text
        help_text = QLabel("💡 Tip: Drag and drop drawings to reorder them")
        help_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #64748b;
                background: transparent;
                font-style: italic;
            }
        """)
        left.addWidget(help_text)

        # Add new drawing section
        add_label = QLabel("Add New Drawing")
        add_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
            }
        """)
        
        add_layout = QHBoxLayout()
        self.new_draw = QLineEdit()
        self.new_draw.setPlaceholderText("Drawing name")
        self.new_draw.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #1e293b;
            }
            QLineEdit:focus {
                background: #e2e8f0;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        
        add_btn = QPushButton("+")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedSize(48, 48)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1e3a8a;
            }
        """)
        add_btn.clicked.connect(self.add_drawing)
        self.new_draw.returnPressed.connect(add_btn.click)
        
        add_layout.addWidget(self.new_draw)
        add_layout.addWidget(add_btn)
        
        left.addWidget(add_label)
        left.addLayout(add_layout)

        # Delete drawing button
        delete_drawing_btn = QPushButton("🗑 Delete Selected Drawing")
        delete_drawing_btn.setCursor(Qt.PointingHandCursor)
        delete_drawing_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 10px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #fef2f2;
            }
        """)
        delete_drawing_btn.clicked.connect(self.delete_drawing)
        left.addWidget(delete_drawing_btn)

        # ===== CENTER: SUB-STEPS =====
        center_frame = QFrame()
        center_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        
        center = QVBoxLayout(center_frame)
        center.setContentsMargins(32, 32, 32, 32)
        center.setSpacing(16)
        
        center_title = QLabel("Sub-Steps")
        center_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        center.addWidget(center_title)

        # FIX #6: Enable drag and drop for substeps too
        self.substeps = QListWidget()
        self.substeps.setDragDropMode(QListWidget.InternalMove)
        self.substeps.setDefaultDropAction(Qt.MoveAction)
        self.substeps.setStyleSheet("""
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 0;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 16px 20px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-bottom: 10px;
                background: #f8fafc;
                color: #1e293b;
            }
            QListWidget::item:hover {
                background: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            QListWidget::item:selected {
                background: white;
                border: 2px solid #1e40af;
                color: #1e293b;
            }
        """)
        # FIX #6: Connect to save new order when substeps are moved
        self.substeps.model().rowsMoved.connect(self.save_substep_order)
        
        # Empty state for substeps
        self.empty_substeps = QLabel("← Select a drawing to view its sub-steps")
        self.empty_substeps.setAlignment(Qt.AlignCenter)
        self.empty_substeps.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                font-style: italic;
                background: transparent;
                padding: 60px 20px;
            }
        """)
        
        center.addWidget(self.substeps)
        center.addWidget(self.empty_substeps)
        
        self.substeps.hide()

        # Reordering help text for substeps
        substep_help_text = QLabel("💡 Tip: Drag and drop sub-steps to reorder them")
        substep_help_text.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #64748b;
                background: transparent;
                font-style: italic;
            }
        """)
        center.addWidget(substep_help_text)

        # ===== RIGHT: SUB-STEP CONTROLS =====
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: none;
                border-radius: 12px;
            }
        """)
        
        right = QVBoxLayout(right_frame)
        right.setContentsMargins(32, 32, 32, 32)
        right.setSpacing(16)
        
        right_title = QLabel("Manage Sub-Steps")
        right_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                background: transparent;
            }
        """)
        right.addWidget(right_title)

        # Drawing name display
        drawing_label = QLabel("Current Drawing:")
        drawing_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #64748b;
                background: transparent;
            }
        """)
        
        self.drawing_display = QLabel("(No drawing selected)")
        self.drawing_display.setStyleSheet("""
            QLabel {
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #64748b;
                font-style: italic;
            }
        """)
        
        right.addWidget(drawing_label)
        right.addWidget(self.drawing_display)

        # Add substep section
        add_substep_label = QLabel("Add New Sub-Step")
        add_substep_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                background: transparent;
                margin-top: 16px;
            }
        """)
        
        self.substep_name = QLineEdit()
        self.substep_name.setPlaceholderText("Sub-step name")
        self.substep_name.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background: #f1f5f9;
                color: #1e293b;
            }
            QLineEdit:focus {
                background: #e2e8f0;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        
        self.add_substep_btn = QPushButton("+ Add Sub-Step")
        self.add_substep_btn.setCursor(Qt.PointingHandCursor)
        self.add_substep_btn.setEnabled(False)
        self.add_substep_btn.setStyleSheet("""
            QPushButton {
                background: #1e40af;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover:enabled {
                background: #1e3a8a;
            }
            QPushButton:disabled {
                background: #cbd5e1;
                color: #94a3b8;
            }
        """)
        self.add_substep_btn.clicked.connect(self.add_substep)
        self.substep_name.returnPressed.connect(self.add_substep_btn.click)
        
        right.addWidget(add_substep_label)
        right.addWidget(self.substep_name)
        right.addWidget(self.add_substep_btn)

        # Delete substep button
        delete_substep_btn = QPushButton("🗑 Delete Selected Sub-Step")
        delete_substep_btn.setCursor(Qt.PointingHandCursor)
        delete_substep_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 10px;
                font-weight: 600;
                font-size: 13px;
                margin-top: 12px;
            }
            QPushButton:hover {
                background: #fef2f2;
            }
        """)
        delete_substep_btn.clicked.connect(self.delete_substep)
        right.addWidget(delete_substep_btn)

        right.addStretch()

        # Add frames to main layout with proper sizing
        root.addWidget(left_frame, 2)
        root.addWidget(center_frame, 2)
        root.addWidget(right_frame, 1)

        # Load initial data
        self.load_template()

    def sync_template_to_projects(self, change_type, drawing_id=None, drawing_data=None, step_id=None, step_data=None):
        """
        CHANGE 1: Sync template changes to all existing projects.
        Called whenever admin adds/deletes a drawing or substep in the template.

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
                        # Only add if it doesn't already exist in this project
                        existing = self.fb.get_drawing(project_id, drawing_id)
                        if not existing:
                            # Build substeps with completed=False
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
                            # Only auto-delete if not yet started — safety measure
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
                                # Only delete if substep hasn't been completed yet
                                self.fb.root.child("drawings").child(project_id).child(drawing_id) \
                                    .child("sub_steps").child(step_id).delete()
                                updated += 1

                except Exception as proj_err:
                    logger.warning(f"Could not sync to project {project_id}: {proj_err}")

            logger.info(f"Template sync '{change_type}': updated {updated}/{len(all_projects)} projects")

        except Exception as e:
            logger.error(f"Template sync failed for '{change_type}': {e}")

    def load_template(self):
        """Load all drawings from template - FIX #4: sorted by order"""
        self.drawings.clear()
        
        try:
            template = self.fb.get_project_template()
            
            # FIX #4: Sort drawings by order field
            drawings_list = []
            for drawing_id, drawing in template.items():
                order = drawing.get('order', 999)
                drawings_list.append((order, drawing_id, drawing))
            
            drawings_list.sort(key=lambda x: x[0])
            
            for order, drawing_id, drawing in drawings_list:
                substeps_count = len(drawing.get('sub_steps', {}))
                
                # FIX #2: Format with substep count
                display_text = f"{drawing['name']}\n{substeps_count} sub-steps"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, drawing_id)
                self.drawings.addItem(item)
            
            logger.info(f"Loaded {len(template)} drawings")
            
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")

    def save_drawing_order(self):
        """FIX #4: Save new drawing order after drag-and-drop"""
        try:
            template = self.fb.get_project_template()
            
            # Update order for each drawing based on current position in list
            for index in range(self.drawings.count()):
                item = self.drawings.item(index)
                drawing_id = item.data(Qt.UserRole)
                
                if drawing_id in template:
                    template[drawing_id]['order'] = index
            
            # Save back to database (you might need a batch update method)
            for drawing_id, drawing in template.items():
                self.fb.save_template_drawing(drawing_id, drawing)
            
            logger.info("Saved new drawing order")
            
        except Exception as e:
            logger.error(f"Error saving drawing order: {str(e)}")

    def save_substep_order(self):
        """FIX #6: Save new substep order after drag-and-drop"""
        if not self.selected_drawing_id:
            return
            
        try:
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps = drawing.get('sub_steps', {})
            
            # Update order for each substep based on current position in list
            for index in range(self.substeps.count()):
                item = self.substeps.item(index)
                step_id = item.data(Qt.UserRole)
                
                if step_id in substeps:
                    substeps[step_id]['order'] = index
            
            # Save back to database
            drawing['sub_steps'] = substeps
            self.fb.save_template_drawing(self.selected_drawing_id, drawing)
            
            logger.info(f"Saved new substep order for drawing: {self.selected_drawing_id}")
            
        except Exception as e:
            logger.error(f"Error saving substep order: {str(e)}")

    def load_substeps(self, item):
        """Load sub-steps for selected drawing - FIX #6: sorted by order"""
        drawing_id = item.data(Qt.UserRole)
        self.selected_drawing_id = drawing_id
        
        try:
            template = self.fb.get_project_template()
            drawing = template.get(drawing_id, {})
            
            self.drawing_display.setText(drawing.get('name', 'Unknown'))
            self.drawing_display.setStyleSheet("""
                QLabel {
                    padding: 12px 16px;
                    border-radius: 8px;
                    font-size: 14px;
                    background: #dbeafe;
                    color: #1e40af;
                    font-weight: 600;
                }
            """)
            
            self.substeps.clear()
            self.empty_substeps.hide()
            self.substeps.show()
            
            substeps = drawing.get('sub_steps', {})
            
            # FIX #6: Sort substeps by order field
            substeps_list = []
            for step_id, step in substeps.items():
                order = step.get('order', 999)
                substeps_list.append((order, step_id, step))
            
            substeps_list.sort(key=lambda x: x[0])
            
            for order, step_id, step in substeps_list:
                step_item = QListWidgetItem(step['name'])
                step_item.setData(Qt.UserRole, step_id)
                self.substeps.addItem(step_item)
            
            self.add_substep_btn.setEnabled(True)
            logger.info(f"Loaded {len(substeps)} sub-steps for drawing: {drawing_id}")
            
        except Exception as e:
            logger.error(f"Error loading sub-steps: {str(e)}")

    def update_drawing_substep_count(self):
        """OPTIMIZED: Update only the substep count for the current drawing without full reload"""
        if not self.selected_drawing_id:
            return
            
        try:
            # Find the current drawing item in the list
            current_row = self.drawings.currentRow()
            if current_row < 0:
                return
                
            # Get fresh data from database
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps_count = len(drawing.get('sub_steps', {}))
            
            # Update just this item's text
            current_item = self.drawings.item(current_row)
            display_text = f"{drawing['name']}\n{substeps_count} sub-steps"
            current_item.setText(display_text)
            
            logger.info(f"Updated substep count for drawing: {self.selected_drawing_id}")
            
        except Exception as e:
            logger.error(f"Error updating substep count: {str(e)}")

    def add_drawing(self):
        """OPTIMIZED: Add a new drawing to the template without full reload"""
        name = self.new_draw.text().strip()
        
        if not name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a drawing name")
            return
        
        try:
            drawing_id = str(uuid.uuid4())
            
            # FIX #4: Set order to end of list
            template = self.fb.get_project_template()
            max_order = max([d.get('order', 0) for d in template.values()], default=-1)
            
            drawing_data = {
                "name": name,
                "sub_steps": {},
                "order": max_order + 1
            }
            
            self.fb.save_template_drawing(drawing_id, drawing_data)
            logger.info(f"Added drawing: {drawing_id}")

            self.new_draw.clear()

            # OPTIMIZED: Just add the new item to the list instead of full reload
            display_text = f"{name}\n0 sub-steps"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, drawing_id)
            self.drawings.addItem(item)

            # Automatically select the new drawing
            self.drawings.setCurrentItem(item)

            # CHANGE 1: Sync new drawing to all existing projects
            self.sync_template_to_projects('add_drawing', drawing_id=drawing_id, drawing_data=drawing_data)
            
        except Exception as e:
            logger.error(f"Error adding drawing: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to add drawing: {str(e)}")

    def delete_drawing(self):
        """Delete selected drawing from template"""
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

                # CHANGE 1: Sync deletion to all existing projects (only removes not_started ones)
                self.sync_template_to_projects('delete_drawing', drawing_id=drawing_id)

                self.selected_drawing_id = None
                self.drawing_display.setText("(No drawing selected)")
                self.drawing_display.setStyleSheet("""
                    QLabel {
                        padding: 12px 16px;
                        border-radius: 8px;
                        font-size: 14px;
                        background: #f1f5f9;
                        color: #64748b;
                        font-style: italic;
                    }
                """)
                self.substeps.hide()
                self.empty_substeps.show()
                self.add_substep_btn.setEnabled(False)
                self.load_template()
                
            except Exception as e:
                logger.error(f"Error deleting drawing: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to delete drawing: {str(e)}")

    def add_substep(self):
        """OPTIMIZED: Add a new sub-step and immediately show it without full reload"""
        if not self.selected_drawing_id:
            ModernMessageBox.warning(self, "No Drawing Selected", "Please select a drawing first")
            return
        
        name = self.substep_name.text().strip()
        
        if not name:
            ModernMessageBox.warning(self, "Validation Error", "Please enter a sub-step name")
            return
        
        try:
            step_id = str(uuid.uuid4())
            
            # Get current substeps to determine order
            template = self.fb.get_project_template()
            drawing = template.get(self.selected_drawing_id, {})
            substeps = drawing.get('sub_steps', {})
            
            # Set order to end of list
            max_order = max([s.get('order', 0) for s in substeps.values()], default=-1)
            
            step_data = {
                "name": name,
                "completed": False,
                "order": max_order + 1
            }
            
            self.fb.add_template_substep(self.selected_drawing_id, step_id, step_data)
            logger.info(f"Added sub-step: {step_id}")

            # Clear input
            self.substep_name.clear()

            # OPTIMIZED: Just add the new item to the list instead of reloading everything
            step_item = QListWidgetItem(name)
            step_item.setData(Qt.UserRole, step_id)
            self.substeps.addItem(step_item)

            # Update the substep count in the drawing list (without full reload)
            self.update_drawing_substep_count()

            # CHANGE 1: Sync new substep to all existing projects
            self.sync_template_to_projects('add_substep', drawing_id=self.selected_drawing_id,
                                           step_id=step_id, step_data=step_data)
            
        except Exception as e:
            logger.error(f"Error adding sub-step: {str(e)}")
            ModernMessageBox.error(self, "Error", f"Failed to add sub-step: {str(e)}")

    def delete_substep(self):
        """OPTIMIZED: Delete selected sub-step without full reload"""
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

                # OPTIMIZED: Just remove the item from the list instead of reloading everything
                row = self.substeps.row(selected)
                self.substeps.takeItem(row)

                # Update the substep count in the drawing list (without full reload)
                self.update_drawing_substep_count()

                # CHANGE 1: Sync substep deletion to all existing projects
                self.sync_template_to_projects('delete_substep', drawing_id=self.selected_drawing_id,
                                               step_id=step_id)
                
            except Exception as e:
                logger.error(f"Error deleting sub-step: {str(e)}")
                ModernMessageBox.error(self, "Error", f"Failed to delete sub-step: {str(e)}")