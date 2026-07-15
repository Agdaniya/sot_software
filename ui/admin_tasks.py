"""
AdminTasks — Assign ad-hoc tasks to employees.

Layout
------
Left panel  : scrollable list of all employees.
              Each row shows name + role + counts of open projects & pending tasks.
Right panel : task form (when an employee is selected) + list of tasks already assigned.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QListWidgetItem, QLineEdit,
    QTextEdit, QScrollArea, QSizePolicy, QComboBox,
)
from PySide6.QtCore import Qt, QSize
from datetime import datetime
import uuid

from services.firebase_client import FirebaseClient
import utils.theme as T


# ── Task status meta ──────────────────────────────────────────────────────────
_TASK_STATUS = {
    "pending":     ("Pending",     "#fef9c3", "#92400e"),
    "in_progress": ("In Progress", "#ede9fe", "#5b21b6"),
    "done":        ("Done",        "#ccfbf1", "#0f766e"),
    "closed":      ("Closed",      "#f3f4f6", "#6b7280"),
}


def _task_pill(status: str):
    return _TASK_STATUS.get(status, ("Unknown", "#f3f4f6", "#6b7280"))


# ── Employee row widget ───────────────────────────────────────────────────────
class EmployeeRowWidget(QWidget):
    def __init__(self, username, role, project_count, task_count, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 11, 16, 11)
        outer.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(6)

        name_lbl = QLabel(username)
        name_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {T.TEXT};"
        )
        top.addWidget(name_lbl, 1)

        fg, bg = T.ROLE_COLORS.get(role, (T.TEXT_SEC, T.BG))
        role_badge = QLabel(role.replace("_", " ").title())
        role_badge.setStyleSheet(
            f"background: {bg}; color: {fg}; border-radius: 4px; "
            f"padding: 1px 7px; font-size: 10px; font-weight: 700;"
        )
        top.addWidget(role_badge)
        outer.addLayout(top)

        info = QLabel(
            f"{project_count} project{'s' if project_count != 1 else ''}  ·  "
            f"{task_count} pending task{'s' if task_count != 1 else ''}"
        )
        info.setStyleSheet(f"font-size: 11px; color: {T.TEXT_SEC};")
        outer.addWidget(info)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")


# ── Task row widget ───────────────────────────────────────────────────────────
class TaskRowWidget(QWidget):
    def __init__(self, title, description, due_date, status, created_by_name,
                 on_status_change, on_close, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)

        is_closed = (status == "closed")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(6)

        # ── Row 1: title + pill + close btn ──────────────────────────────────
        r1 = QHBoxLayout()
        r1.setSpacing(8)

        title_lbl = QLabel(title)
        if is_closed:
            title_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {T.TEXT_HINT}; "
                f"text-decoration: line-through;"
            )
        else:
            title_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 600; color: {T.TEXT};"
            )
        r1.addWidget(title_lbl, 1)

        label, pill_bg, pill_fg = _task_pill(status)
        pill = QLabel(f"● {label}")
        pill.setStyleSheet(
            f"font-size: 10px; font-weight: 700; padding: 2px 10px; "
            f"border-radius: 10px; background: {pill_bg}; color: {pill_fg};"
        )
        r1.addWidget(pill)

        if not is_closed:
            close_btn = QPushButton("✕  Close")
            close_btn.setFixedHeight(24)
            close_btn.setCursor(Qt.PointingHandCursor)
            close_btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {T.TEXT_HINT}; "
                f"border: 1px solid {T.BORDER_SOLID}; border-radius: 4px; "
                f"font-size: 10px; font-weight: 600; padding: 0 8px; }}"
                f"QPushButton:hover {{ background: {T.DANGER_BG}; color: {T.DANGER}; "
                f"border-color: #fecaca; }}"
            )
            close_btn.clicked.connect(lambda _checked=False: on_close())
            r1.addWidget(close_btn)
        outer.addLayout(r1)

        # ── Row 2: description ────────────────────────────────────────────────
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setWordWrap(True)
            if is_closed:
                desc_lbl.setStyleSheet(
                    f"font-size: 12px; color: {T.TEXT_HINT}; "
                    f"text-decoration: line-through;"
                )
            else:
                desc_lbl.setStyleSheet(
                    f"font-size: 12px; color: {T.TEXT_SEC}; line-height: 1.5;"
                )
            outer.addWidget(desc_lbl)

        # ── Row 3: meta + status changer (hidden when closed) ─────────────────
        r3 = QHBoxLayout()
        r3.setSpacing(12)

        meta = []
        if due_date:
            meta.append(f"Due: {due_date}")
        if created_by_name:
            meta.append(f"By: {created_by_name}")
        if meta:
            meta_lbl = QLabel("  ·  ".join(meta))
            meta_lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_HINT};")
            r3.addWidget(meta_lbl)

        r3.addStretch()

        if not is_closed:
            status_combo = QComboBox()
            for key, (lbl, *_) in _TASK_STATUS.items():
                if key == "closed":
                    continue          # closed is set only via the close button
                status_combo.addItem(lbl, key)
            idx = status_combo.findData(status)
            if idx >= 0:
                status_combo.setCurrentIndex(idx)
            status_combo.setFixedHeight(26)
            status_combo.setStyleSheet(
                f"QComboBox {{ background: {T.BG}; border: 1px solid {T.BORDER_SOLID}; "
                f"border-radius: 4px; font-size: 11px; font-weight: 600; "
                f"color: {T.TEXT_SEC}; padding: 0 6px; }}"
                f"QComboBox::drop-down {{ border: none; width: 18px; }}"
                f"QComboBox::down-arrow {{ border-left: 4px solid transparent; "
                f"border-right: 4px solid transparent; "
                f"border-top: 4px solid {T.TEXT_SEC}; margin-right: 4px; }}"
                f"QComboBox QAbstractItemView {{ background: {T.SURFACE}; "
                f"border: 1px solid {T.BORDER_SOLID}; font-size: 12px; }}"
            )
            status_combo.currentIndexChanged.connect(
                lambda _: on_status_change(status_combo.currentData())
            )
            r3.addWidget(status_combo)

        outer.addLayout(r3)

        self.setStyleSheet("QWidget { background: transparent; border: none; }")


# ── Main page ─────────────────────────────────────────────────────────────────
class AdminTasks(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.fb           = FirebaseClient()
        self.selected_uid = None
        self._all_users   = {}
        self._all_projects = {}
        self._all_tasks   = {}

        self.setStyleSheet(T.app_base())

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        from ui.admin_dashboard import make_topbar
        topbar, back_btn = make_topbar(
            self, current_user, None, show_back=True, back_title="Tasks"
        )
        main.addWidget(topbar)
        if back_btn:
            back_btn.clicked.connect(self._go_back)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"QWidget {{ background: {T.BG}; }}")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ── LEFT: employee list ───────────────────────────────────────────────
        left = QFrame()
        left.setFixedWidth(300)
        left.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-right: 1px solid {T.BORDER_SOLID}; }}"
        )
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        lhdr = QFrame()
        lhdr.setFixedHeight(56)
        lhdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        lhdr_l = QHBoxLayout(lhdr)
        lhdr_l.setContentsMargins(20, 0, 20, 0)
        lhdr_l.setSpacing(8)
        lhdr_title = QLabel("Employees")
        lhdr_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        self._emp_count_lbl = QLabel("0")
        self._emp_count_lbl.setStyleSheet(
            f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        lhdr_l.addWidget(lhdr_title)
        lhdr_l.addWidget(self._emp_count_lbl)
        lhdr_l.addStretch()
        left_layout.addWidget(lhdr)

        sf = QFrame()
        sf.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        sfl = QVBoxLayout(sf)
        sfl.setContentsMargins(12, 10, 12, 10)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search employees…")
        self._search.setMinimumHeight(34)
        self._search.setStyleSheet(T.input_field_flat())
        self._search.textChanged.connect(self._filter_employees)
        sfl.addWidget(self._search)
        left_layout.addWidget(sf)

        self._emp_list = QListWidget()
        self._emp_list.setStyleSheet(
            f"QListWidget {{ border: none; background: {T.SURFACE}; outline: none; }}"
            f"QListWidget::item {{ border: none; margin: 0; padding: 0; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
            f"QListWidget::item:hover {{ background: {T.BG}; }}"
            f"QListWidget::item:selected {{ background: #f0f6ff; "
            f"border-left: 3px solid #3b82f6; }}"
        )
        self._emp_list.itemClicked.connect(self._on_employee_selected)
        left_layout.addWidget(self._emp_list, 1)
        body_layout.addWidget(left)

        # ── RIGHT panel ───────────────────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(f"QFrame {{ background: {T.BG}; border: none; }}")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        rhdr = QFrame()
        rhdr.setFixedHeight(56)
        rhdr.setStyleSheet(
            f"QFrame {{ background: {T.SURFACE}; border: none; "
            f"border-bottom: 1px solid {T.BORDER_SOLID}; }}"
        )
        rhdr_l = QHBoxLayout(rhdr)
        rhdr_l.setContentsMargins(24, 0, 24, 0)
        self._right_title = QLabel("Select an employee")
        self._right_title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {T.TEXT};"
        )
        rhdr_l.addWidget(self._right_title)
        rhdr_l.addStretch()
        right_layout.addWidget(rhdr)

        # Empty state
        self._empty_state = QLabel(
            "Select an employee on the left to assign tasks\nor view their current workload."
        )
        self._empty_state.setAlignment(Qt.AlignCenter)
        self._empty_state.setWordWrap(True)
        self._empty_state.setStyleSheet(
            f"color: {T.TEXT_HINT}; font-size: 13px; padding: 60px;"
        )
        right_layout.addWidget(self._empty_state, 1)

        # ── Scroll area — holds everything after header ───────────────────────
        self._right_scroll = QScrollArea()
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        self._right_scroll.hide()

        self._right_content = QWidget()
        self._right_content.setStyleSheet(
            f"QWidget {{ background: {T.BG}; }}"
        )
        self._rc_layout = QVBoxLayout(self._right_content)
        self._rc_layout.setContentsMargins(28, 24, 28, 28)
        self._rc_layout.setSpacing(0)
        self._rc_layout.setAlignment(Qt.AlignTop)

        # ── Workload section ──────────────────────────────────────────────────
        wl_section_lbl = QLabel("CURRENT WORKLOAD")
        wl_section_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {T.TEXT_HINT}; "
            f"letter-spacing: 1.2px;"
        )
        self._rc_layout.addWidget(wl_section_lbl)
        self._rc_layout.addSpacing(10)

        self._workload_row = QHBoxLayout()
        self._workload_row.setSpacing(24)
        self._rc_layout.addLayout(self._workload_row)
        self._rc_layout.addSpacing(24)

        # separator
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        self._rc_layout.addWidget(sep1)
        self._rc_layout.addSpacing(24)

        # ── Assign task form ──────────────────────────────────────────────────
        form_title = QLabel("Assign New Task")
        form_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {T.TEXT};"
        )
        self._rc_layout.addWidget(form_title)
        self._rc_layout.addSpacing(16)

        self._rc_layout.addWidget(self._field_lbl("Task Title"))
        self._rc_layout.addSpacing(6)
        self._task_title = QLineEdit()
        self._task_title.setPlaceholderText("Short summary of the task")
        self._task_title.setMinimumHeight(38)
        self._task_title.setStyleSheet(T.input_field())
        self._rc_layout.addWidget(self._task_title)
        self._rc_layout.addSpacing(12)

        self._rc_layout.addWidget(self._field_lbl("Description (optional)"))
        self._rc_layout.addSpacing(6)
        self._task_desc = QTextEdit()
        self._task_desc.setPlaceholderText("Any details, context, or notes…")
        self._task_desc.setFixedHeight(88)
        self._task_desc.setStyleSheet(T.input_field())
        self._rc_layout.addWidget(self._task_desc)
        self._rc_layout.addSpacing(12)

        self._rc_layout.addWidget(self._field_lbl("Due Date (optional)"))
        self._rc_layout.addSpacing(6)
        self._task_due = QLineEdit()
        self._task_due.setPlaceholderText("e.g. 2025-07-15 or ASAP")
        self._task_due.setMinimumHeight(38)
        self._task_due.setStyleSheet(T.input_field())
        self._rc_layout.addWidget(self._task_due)
        self._rc_layout.addSpacing(8)

        self._form_error = QLabel("")
        self._form_error.setStyleSheet(
            f"QLabel {{ color: {T.DANGER}; background: {T.DANGER_BG}; "
            f"border: 1px solid #FECDD3; border-radius: {T.RADIUS_SM}; "
            f"padding: 8px 12px; font-size: 12px; }}"
        )
        self._form_error.hide()
        self._rc_layout.addWidget(self._form_error)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._assign_btn = QPushButton("Assign Task")
        self._assign_btn.setMinimumHeight(38)
        self._assign_btn.setCursor(Qt.PointingHandCursor)
        self._assign_btn.setStyleSheet(T.btn_primary())
        self._assign_btn.clicked.connect(self._handle_assign)
        btn_row.addWidget(self._assign_btn)
        self._rc_layout.addLayout(btn_row)
        self._rc_layout.addSpacing(28)

        # separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
        self._rc_layout.addWidget(sep2)
        self._rc_layout.addSpacing(20)

        # ── Assigned tasks header ─────────────────────────────────────────────
        tasks_hdr_row = QHBoxLayout()
        self._tasks_section_lbl = QLabel("ASSIGNED TASKS")
        self._tasks_section_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {T.TEXT_HINT}; letter-spacing: 1.2px;"
        )
        self._tasks_count_badge = QLabel("")
        self._tasks_count_badge.setStyleSheet(
            f"background: {T.BG}; color: {T.TEXT_SEC}; border-radius: 10px; "
            f"padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        self._tasks_count_badge.hide()
        tasks_hdr_row.addWidget(self._tasks_section_lbl)
        tasks_hdr_row.addWidget(self._tasks_count_badge)
        tasks_hdr_row.addStretch()
        self._rc_layout.addLayout(tasks_hdr_row)
        self._rc_layout.addSpacing(10)

        # ── Task rows container (plain VBox — grows with content) ─────────────
        self._tasks_container = QWidget()
        self._tasks_container.setStyleSheet(
            f"QWidget {{ background: {T.SURFACE}; border: none; }}"
        )
        self._tasks_vbox = QVBoxLayout(self._tasks_container)
        self._tasks_vbox.setContentsMargins(0, 0, 0, 0)
        self._tasks_vbox.setSpacing(0)

        self._no_tasks_lbl = QLabel("No tasks assigned yet.")
        self._no_tasks_lbl.setAlignment(Qt.AlignCenter)
        self._no_tasks_lbl.setStyleSheet(
            f"color: {T.TEXT_HINT}; font-size: 12px; padding: 24px;"
        )
        self._tasks_vbox.addWidget(self._no_tasks_lbl)

        self._rc_layout.addWidget(self._tasks_container)

        self._right_scroll.setWidget(self._right_content)
        right_layout.addWidget(self._right_scroll, 1)

        body_layout.addWidget(right, 1)
        main.addWidget(body, 1)

        self._load_data()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _go_back(self):
        mw = self.window()
        if hasattr(mw, "go_back"):
            mw.go_back()

    def _field_lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {T.TEXT_SEC}; "
            f"letter-spacing: 0.4px; text-transform: uppercase;"
        )
        return lbl

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_data(self):
        try:
            self._all_users    = self.fb.get_all_users()
            self._all_projects = self.fb.get_all_projects()
            self._all_tasks    = self.fb.get_all_tasks()
        except Exception:
            self._all_users    = {}
            self._all_projects = {}
            self._all_tasks    = {}
        self._populate_employee_list()

    def _project_count_for(self, uid):
        return sum(
            1 for p in self._all_projects.values()
            if uid in p.get("assigned_users", {})
        )

    def _pending_task_count_for(self, uid):
        return sum(
            1 for t in self._all_tasks.values()
            if t.get("assigned_to") == uid and t.get("status") not in ("done", "closed")
        )

    def _populate_employee_list(self):
        self._emp_list.clear()
        employees = {
            uid: u for uid, u in self._all_users.items()
            if u.get("role") == "employee"
        }
        self._emp_count_lbl.setText(str(len(employees)))
        self._emp_count_lbl.setVisible(bool(employees))

        for uid, user in sorted(employees.items(), key=lambda x: x[1].get("username", "").lower()):
            pc = self._project_count_for(uid)
            tc = self._pending_task_count_for(uid)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, uid)
            item.setData(Qt.UserRole + 1, user.get("username", "").lower())
            w = EmployeeRowWidget(user.get("username", uid), user.get("role", "employee"), pc, tc)
            hint = w.sizeHint()
            item.setSizeHint(QSize(hint.width(), max(hint.height(), 68)))
            self._emp_list.addItem(item)
            self._emp_list.setItemWidget(item, w)

    def _filter_employees(self, text):
        lo = text.lower()
        for i in range(self._emp_list.count()):
            item = self._emp_list.item(i)
            name = item.data(Qt.UserRole + 1) or ""
            item.setHidden(lo not in name)

    # ── Employee selected ─────────────────────────────────────────────────────
    def _on_employee_selected(self, item):
        uid  = item.data(Qt.UserRole)
        user = self._all_users.get(uid, {})
        self.selected_uid = uid
        self._right_title.setText(f"Tasks — {user.get('username', uid)}")
        self._empty_state.hide()
        self._right_scroll.show()
        self._refresh_workload(uid)
        self._refresh_tasks(uid)

    def _refresh_workload(self, uid):
        while self._workload_row.count():
            item = self._workload_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # clean nested layouts
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        projects = [
            p.get("name", "Unnamed")
            for p in self._all_projects.values()
            if uid in p.get("assigned_users", {})
        ]
        pending_tasks = [
            t for t in self._all_tasks.values()
            if t.get("assigned_to") == uid and t.get("status") not in ("done", "closed")
        ]

        for label, value, color in [
            ("Active Projects", str(len(projects)),     T.INDIGO),
            ("Pending Tasks",   str(len(pending_tasks)), T.WARNING),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(
                f"font-size: 26px; font-weight: 700; color: {color};"
            )
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {T.TEXT_SEC};")
            col.addWidget(val_lbl)
            col.addWidget(lbl)
            self._workload_row.addLayout(col)

        if projects:
            sep = QFrame()
            sep.setFixedSize(1, 44)
            sep.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
            self._workload_row.addWidget(sep)

            proj_col = QVBoxLayout()
            proj_col.setSpacing(2)
            proj_hdr = QLabel("Projects")
            proj_hdr.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {T.TEXT_SEC};")
            proj_col.addWidget(proj_hdr)
            for pname in projects:
                p_lbl = QLabel(f"• {pname}")
                p_lbl.setStyleSheet(f"font-size: 12px; color: {T.TEXT};")
                proj_col.addWidget(p_lbl)
            self._workload_row.addLayout(proj_col)

        self._workload_row.addStretch()

    def _refresh_tasks(self, uid):
        # clear all widgets (task rows + separator QFrames)
        while self._tasks_vbox.count():
            item = self._tasks_vbox.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        self._all_tasks = self.fb.get_all_tasks()
        user_tasks = {
            tid: t for tid, t in self._all_tasks.items()
            if t.get("assigned_to") == uid
        }

        count = len(user_tasks)
        self._tasks_count_badge.setText(str(count))
        self._tasks_count_badge.setVisible(count > 0)

        if not user_tasks:
            self._no_tasks_lbl = QLabel("No tasks assigned yet.")
            self._no_tasks_lbl.setAlignment(Qt.AlignCenter)
            self._no_tasks_lbl.setStyleSheet(
                f"color: {T.TEXT_HINT}; font-size: 12px; padding: 24px;"
            )
            self._tasks_vbox.addWidget(self._no_tasks_lbl)
            return

        def _sort_key(item):
            order = {"pending": 0, "in_progress": 1, "done": 2, "closed": 3}
            return (order.get(item[1].get("status", "pending"), 9),
                    item[1].get("created_at", ""))

        for i, (tid, task) in enumerate(sorted(user_tasks.items(), key=_sort_key)):
            creator_name = ""
            creator = self._all_users.get(task.get("created_by", ""), {})
            if creator:
                creator_name = creator.get("username", "")

            row_widget = TaskRowWidget(
                title           = task.get("title", "Untitled"),
                description     = task.get("description", ""),
                due_date        = task.get("due_date", ""),
                status          = task.get("status", "pending"),
                created_by_name = creator_name,
                on_status_change= lambda new_status, t=tid: self._change_task_status(t, new_status),
                on_close        = lambda t=tid: self._close_task(t),
            )

            # separator between rows
            if i > 0:
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {T.BORDER_SOLID}; border: none;")
                self._tasks_vbox.addWidget(sep)

            self._tasks_vbox.addWidget(row_widget)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _handle_assign(self):
        if not self.selected_uid:
            return

        title = self._task_title.text().strip()
        if not title:
            self._form_error.setText("Task title is required.")
            self._form_error.show()
            return
        self._form_error.hide()

        task_id = f"task_{uuid.uuid4().hex[:12]}"
        data = {
            "task_id":     task_id,
            "title":       title,
            "description": self._task_desc.toPlainText().strip(),
            "due_date":    self._task_due.text().strip(),
            "assigned_to": self.selected_uid,
            "created_by":  self.current_user.get("user_id", "") if self.current_user else "",
            "status":      "pending",
            "created_at":  datetime.now().isoformat(),
        }

        try:
            self.fb.assign_task(task_id, data)
            self._task_title.clear()
            self._task_desc.clear()
            self._task_due.clear()
            self._all_tasks = self.fb.get_all_tasks()
            self._refresh_workload(self.selected_uid)
            self._refresh_tasks(self.selected_uid)
            self._populate_employee_list()
        except Exception as e:
            self._form_error.setText(f"Failed to assign task: {str(e)}")
            self._form_error.show()

    def _change_task_status(self, task_id, new_status):
        try:
            self.fb.update_task_status(task_id, new_status)
            self._all_tasks = self.fb.get_all_tasks()
            if self.selected_uid:
                self._refresh_workload(self.selected_uid)
                self._refresh_tasks(self.selected_uid)
            self._populate_employee_list()
        except Exception as e:
            from utils.modern_dialogs import ModernMessageBox
            ModernMessageBox.error(self, "Error", f"Could not update task: {str(e)}")

    def _close_task(self, task_id):
        try:
            self.fb.update_task_status(task_id, "closed")
            self._all_tasks = self.fb.get_all_tasks()
            if self.selected_uid:
                self._refresh_workload(self.selected_uid)
                self._refresh_tasks(self.selected_uid)
            self._populate_employee_list()
        except Exception as e:
            from utils.modern_dialogs import ModernMessageBox
            ModernMessageBox.error(self, "Error", f"Could not close task: {str(e)}")
