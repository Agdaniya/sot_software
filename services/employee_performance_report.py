from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime
from services.firebase_client import FirebaseClient
from utils.logger import logger
import os


def get_reports_directory():
    try:
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        reports_dir = os.path.join(documents, 'SOT_Reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        return reports_dir
    except Exception as e:
        logger.warning(f"Could not use Documents folder: {e}, falling back to home directory")
        home_reports = os.path.join(os.path.expanduser('~'), 'SOT_Reports')
        if not os.path.exists(home_reports):
            os.makedirs(home_reports)
        return home_reports


# ── Shared palette (calm, professional) ───────────────────────────────────────

def fill(hex_color):
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")

CHARCOAL   = fill("2d3748")   # primary header
DARK_SLATE = fill("3d4f63")   # section header A
STEEL      = fill("4a5568")   # section header B
MIST       = fill("f7f9fb")   # meta / summary rows
ROW_WHITE  = fill("ffffff")
ROW_ALT    = fill("f4f6f8")

STATUS_FILL = {
    "not_started":     fill("edf0f2"),
    "in_progress":     fill("fef9ec"),
    "submitted":       fill("ede9fe"),
    "admin_rejected":  fill("fdf0f0"),
    "admin_approved":  fill("edfaf3"),
    "client_approved": fill("e6f4ef"),
}
STATUS_COLOR = {
    "not_started":     "6b7a8d",
    "in_progress":     "8a6800",
    "submitted":       "5b21b6",
    "admin_rejected":  "9b1c1c",
    "admin_approved":  "1a6b43",
    "client_approved": "065f46",
}

NO_BORDER   = Border()
BOTTOM_LINE = Border(bottom=Side(style="thin", color="dde3ea"))

NCOLS = 10   # columns A–J


# ── Helpers ───────────────────────────────────────────────────────────────────

def _blank(ws, row, bg=None, border=BOTTOM_LINE):
    for col in range(1, NCOLS + 1):
        c = ws.cell(row=row, column=col)
        c.border = border
        if bg:
            c.fill = bg


def _c(ws, row, col, value="", fg="2d3748", size=10, bold=False,
       italic=False, bg=None, border=BOTTOM_LINE, ah="left", av="center"):
    c = ws.cell(row=row, column=col, value=value)
    c.font      = Font(bold=bold, italic=italic, color=fg, size=size, name="Arial")
    c.alignment = Alignment(horizontal=ah, vertical=av)
    c.border    = border
    if bg:
        c.fill = bg
    return c


def _emp_header(ws, row, username):
    _blank(ws, row, bg=CHARCOAL, border=NO_BORDER)
    c = ws.cell(row=row, column=1, value=f"  {username.upper()}")
    c.fill = CHARCOAL
    c.font = Font(bold=True, color="FFFFFF", size=12, name="Arial")
    c.alignment = Alignment(vertical="center", horizontal="left")
    c.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NCOLS)
    ws.row_dimensions[row].height = 26


def _meta(ws, row, email, role):
    _blank(ws, row, bg=MIST, border=NO_BORDER)
    c1 = ws.cell(row=row, column=1, value=f"  {email}")
    c1.fill = MIST; c1.font = Font(color="6b7a8d", size=9, name="Arial", italic=True)
    c1.alignment = Alignment(vertical="center"); c1.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c2 = ws.cell(row=row, column=6, value=role)
    c2.fill = MIST; c2.font = Font(color="6b7a8d", size=9, name="Arial", italic=True)
    c2.alignment = Alignment(horizontal="right", vertical="center"); c2.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=NCOLS)
    ws.row_dimensions[row].height = 17
    ws.row_dimensions[row].outline_level = 1


def _sec_hdr(ws, row, label, bg_fill, outline_level=1):
    _blank(ws, row, bg=bg_fill, border=NO_BORDER)
    c = ws.cell(row=row, column=1, value=f"  {label}")
    c.fill = bg_fill; c.font = Font(bold=True, color="FFFFFF", size=10, name="Arial")
    c.alignment = Alignment(vertical="center", horizontal="left"); c.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NCOLS)
    ws.row_dimensions[row].height = 20
    ws.row_dimensions[row].outline_level = outline_level


def _col_hdrs(ws, row, cols_map, hidden=True):
    _blank(ws, row, bg=fill("edf0f2"), border=BOTTOM_LINE)
    for col, label in cols_map.items():
        c = ws.cell(row=row, column=col, value=label)
        c.fill = fill("edf0f2"); c.font = Font(bold=True, color="6b7a8d", size=9, name="Arial")
        c.alignment = Alignment(horizontal="center", vertical="center"); c.border = BOTTOM_LINE
    ws.row_dimensions[row].height = 17
    ws.row_dimensions[row].outline_level = 2
    ws.row_dimensions[row].hidden = hidden


def _summary(ws, row, text, outline_level=1):
    _blank(ws, row, bg=MIST, border=NO_BORDER)
    c = ws.cell(row=row, column=1, value=f"  {text}")
    c.fill = MIST; c.font = Font(bold=True, color="4a5568", size=9, name="Arial")
    c.alignment = Alignment(vertical="center", horizontal="left"); c.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NCOLS)
    ws.row_dimensions[row].height = 17
    ws.row_dimensions[row].outline_level = outline_level


def _spacer(ws, row):
    _blank(ws, row, bg=fill("e8ecf0"), border=NO_BORDER)
    ws.row_dimensions[row].height = 10


def _status_chip(ws, row, col, status_key):
    c = ws.cell(row=row, column=col, value=status_key.replace("_", " ").title())
    c.fill = STATUS_FILL.get(status_key, fill("edf0f2"))
    c.font = Font(bold=True, color=STATUS_COLOR.get(status_key, "6b7a8d"), size=9, name="Arial")
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = BOTTOM_LINE


def _pay_chip(ws, row, col, pay_txt, paid):
    c = ws.cell(row=row, column=col, value=pay_txt)
    if pay_txt == "—":
        c.fill = ROW_WHITE; c.font = Font(color="9eaab8", size=9, name="Arial")
    elif paid:
        c.fill = fill("e6f4ef"); c.font = Font(bold=True, color="065f46", size=9, name="Arial")
    else:
        c.fill = fill("fdf0f0"); c.font = Font(bold=True, color="9b1c1c", size=9, name="Arial")
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = BOTTOM_LINE


# ── Main report ────────────────────────────────────────────────────────────────

def generate_employee_performance_report(start_date=None, end_date=None):
    """
    Employee performance report — grouped, collapsible, calm palette.
    Detail rows (level 2) start hidden. Expand with Excel's [+] buttons.
    """
    fb = FirebaseClient()
    users        = fb.root.child("users").get()         or {}
    logs         = fb.root.child("activity_logs").get() or {}
    projects_all = fb.root.child("projects").get()      or {}
    drawings_all = fb.root.child("drawings").get()      or {}

    valid_user_ids = set(users.keys())

    wb = Workbook()
    ws = wb.active
    ws.title = "Employee Report"
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.outlinePr.summaryRight = False

    for letter, width in {
        "A": 3, "B": 22, "C": 22, "D": 22,
        "E": 13, "F": 11, "G": 11, "H": 13, "I": 13, "J": 10
    }.items():
        ws.column_dimensions[letter].width = width

    row = 1
    sorted_users = sorted(
        [(uid, u) for uid, u in users.items() if uid in valid_user_ids],
        key=lambda x: x[1].get("username", "").lower()
    )

    for user_id, user in sorted_users:
        username = user.get("username", "Unknown")
        email    = user.get("email", "")
        role     = user.get("role", "").replace("_", " ").title()

        _emp_header(ws, row, username);  row += 1
        _meta(ws, row, email, role);     row += 1

        # ── ATTENDANCE ──────────────────────────────────────────────────────
        _sec_hdr(ws, row, "Attendance Log", DARK_SLATE, outline_level=1); row += 1
        _col_hdrs(ws, row, {2: "Date", 3: "Login", 4: "Logout",
                             5: "Hours", 6: "Status"}, hidden=True);      row += 1

        user_logs = logs.get(user_id, {}) or {}
        if not isinstance(user_logs, dict):
            user_logs = {}

        total_hours = total_mins = days_worked = 0
        has_att = False

        for idx, log_date in enumerate(sorted(user_logs.keys())):
            if start_date and log_date < start_date: continue
            if end_date   and log_date > end_date:   continue

            entry        = user_logs[log_date]
            login        = entry.get("login_time",  "—")
            logout       = entry.get("logout_time", "—")
            hours_worked = entry.get("total_hours", "—")

            if logout == "—":
                s_txt = "Active";     s_bg = fill("fef9ec"); s_fg = "8a6800"
            elif hours_worked not in ("—", "N/A"):
                s_txt = "Complete";   s_bg = fill("e6f4ef"); s_fg = "065f46"
            else:
                s_txt = "Incomplete"; s_bg = fill("fdf0f0"); s_fg = "9b1c1c"

            if hours_worked not in ("—", "N/A"):
                try:
                    h, m = hours_worked.split(":")
                    total_hours += int(h); total_mins += int(m); days_worked += 1
                except Exception:
                    pass

            rb = ROW_ALT if idx % 2 else ROW_WHITE
            _blank(ws, row, bg=rb, border=BOTTOM_LINE)
            _c(ws, row, 2, log_date,     bg=rb, ah="center")
            _c(ws, row, 3, login,        bg=rb, ah="center")
            _c(ws, row, 4, logout,       bg=rb, ah="center")
            _c(ws, row, 5, hours_worked, bg=rb, ah="center")
            sc = ws.cell(row=row, column=6, value=s_txt)
            sc.fill = s_bg; sc.border = BOTTOM_LINE
            sc.font = Font(bold=True, color=s_fg, size=9, name="Arial")
            sc.alignment = Alignment(horizontal="center", vertical="center")

            ws.row_dimensions[row].height = 16
            ws.row_dimensions[row].outline_level = 2
            ws.row_dimensions[row].hidden = True
            row += 1; has_att = True

        if not has_att:
            _blank(ws, row, bg=ROW_WHITE, border=BOTTOM_LINE)
            c = ws.cell(row=row, column=2, value="No attendance records in this date range")
            c.font = Font(italic=True, color="9eaab8", size=9, name="Arial")
            c.fill = ROW_WHITE; c.border = BOTTOM_LINE
            c.alignment = Alignment(vertical="center")
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            ws.row_dimensions[row].height = 16
            ws.row_dimensions[row].outline_level = 2
            ws.row_dimensions[row].hidden = True
            row += 1

        if days_worked > 0:
            extra_h = total_mins // 60; rem_m = total_mins % 60
            total_h = total_hours + extra_h; avg_h = round(total_h / days_worked, 1)
            _summary(ws, row,
                     f"{days_worked} days worked   ·   {total_h}h {rem_m:02d}m total"
                     f"   ·   avg {avg_h}h / day",
                     outline_level=1)
            row += 1

        # ── DRAWINGS ────────────────────────────────────────────────────────
        _sec_hdr(ws, row, "Drawing Assignments", STEEL, outline_level=1); row += 1

        STATUS_ORDER = {
            "in_progress": 0, "admin_rejected": 1, "not_started": 2,
            "submitted": 3, "admin_approved": 4, "client_approved": 5,
        }

        # Build a dict: project_id → { meta, drawings[] }
        projects_for_user = {}
        for project_id, project in projects_all.items():
            au = project.get("assigned_users", {})
            if not isinstance(au, dict) or user_id not in au:
                continue
            proj_drawings = drawings_all.get(project_id, {})
            if not isinstance(proj_drawings, dict):
                continue
            drawings_list = []
            for drawing_id, drawing in proj_drawings.items():
                d_status  = drawing.get("status", "not_started")
                sub_steps = drawing.get("sub_steps", {})
                total_s   = len(sub_steps)
                done_s    = sum(1 for s in sub_steps.values() if s.get("completed", False))
                progress  = f"{round(done_s / total_s * 100)}%" if total_s else "—"
                paid      = drawing.get("payment_received", False)
                pay_txt   = ("Paid ✓" if paid else "Unpaid ✗") \
                            if d_status == "client_approved" else "—"
                drawings_list.append({
                    "drawing":  drawing.get("name", ""),
                    "status":   d_status,
                    "done":     done_s,
                    "total":    total_s,
                    "progress": progress,
                    "pay_txt":  pay_txt,
                    "paid":     paid if d_status == "client_approved" else None,
                })
            # Sort drawings within each project by status
            drawings_list.sort(key=lambda x: STATUS_ORDER.get(x["status"], 9))
            projects_for_user[project_id] = {
                "name":    project.get("name", ""),
                "client":  project.get("client_name", ""),
                "drawings": drawings_list,
            }

        if not projects_for_user:
            _blank(ws, row, bg=ROW_WHITE, border=BOTTOM_LINE)
            c = ws.cell(row=row, column=2, value="No drawings assigned")
            c.font = Font(italic=True, color="9eaab8", size=9, name="Arial")
            c.fill = ROW_WHITE; c.border = BOTTOM_LINE
            c.alignment = Alignment(vertical="center")
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            ws.row_dimensions[row].height = 16
            ws.row_dimensions[row].outline_level = 2
            ws.row_dimensions[row].hidden = True
            row += 1
        else:
            # Sort projects alphabetically by name
            sorted_projects = sorted(projects_for_user.values(), key=lambda p: p["name"].lower())
            for proj in sorted_projects:
                # ── Project sub-header ──────────────────────────────────────
                _blank(ws, row, bg=fill("dce6f0"), border=NO_BORDER)
                proj_label = f"  📁  {proj['name']}   ·   {proj['client']}"
                pc = ws.cell(row=row, column=2, value=proj_label)
                pc.fill = fill("dce6f0")
                pc.font = Font(bold=True, color="2d3748", size=9, name="Arial")
                pc.alignment = Alignment(vertical="center", horizontal="left")
                pc.border = NO_BORDER
                ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=NCOLS)
                ws.row_dimensions[row].height = 18
                ws.row_dimensions[row].outline_level = 1
                row += 1

                # ── Column headers for this project's drawings ──────────────
                _col_hdrs(ws, row, {3: "Drawing", 4: "Status", 5: "Done",
                                     6: "Total", 7: "Progress", 8: "Payment"},
                          hidden=True)
                row += 1

                if not proj["drawings"]:
                    _blank(ws, row, bg=ROW_WHITE, border=BOTTOM_LINE)
                    c = ws.cell(row=row, column=3, value="No drawings in this project")
                    c.font = Font(italic=True, color="9eaab8", size=9, name="Arial")
                    c.fill = ROW_WHITE; c.border = BOTTOM_LINE
                    c.alignment = Alignment(vertical="center")
                    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=8)
                    ws.row_dimensions[row].height = 16
                    ws.row_dimensions[row].outline_level = 2
                    ws.row_dimensions[row].hidden = True
                    row += 1
                else:
                    for idx, drw in enumerate(proj["drawings"]):
                        rb = ROW_ALT if idx % 2 else ROW_WHITE
                        _blank(ws, row, bg=rb, border=BOTTOM_LINE)
                        _c(ws, row, 3, drw["drawing"],  bg=rb)
                        _status_chip(ws, row, 4, drw["status"])
                        _c(ws, row, 5, drw["done"],     bg=rb, ah="center")
                        _c(ws, row, 6, drw["total"],    bg=rb, ah="center")
                        _c(ws, row, 7, drw["progress"], bg=rb, ah="center")
                        _pay_chip(ws, row, 8, drw["pay_txt"],
                                  paid=drw["paid"] if drw["paid"] is not None else False)
                        ws.row_dimensions[row].height = 17
                        ws.row_dimensions[row].outline_level = 2
                        ws.row_dimensions[row].hidden = True
                        row += 1

        _spacer(ws, row); row += 1

    # ── SUMMARY SHEET ──────────────────────────────────────────────────────────
    ws2 = wb.create_sheet(title="Summary")
    ws2.sheet_view.showGridLines = False
    SN = 7

    for letter, width in {"A": 3, "B": 26, "C": 15, "D": 15,
                          "E": 15, "F": 15, "G": 15}.items():
        ws2.column_dimensions[letter].width = width

    # Title
    for col in range(1, SN + 1):
        c = ws2.cell(row=1, column=col); c.fill = CHARCOAL; c.border = NO_BORDER
    tc = ws2.cell(row=1, column=1, value="  Employee Performance Summary")
    tc.fill = CHARCOAL; tc.border = NO_BORDER
    tc.font = Font(bold=True, color="FFFFFF", size=12, name="Arial")
    tc.alignment = Alignment(vertical="center", horizontal="left")
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=SN)
    ws2.row_dimensions[1].height = 28

    # Column headers
    for col in range(1, SN + 1):
        c = ws2.cell(row=2, column=col); c.fill = fill("edf0f2"); c.border = BOTTOM_LINE
    for col, hdr in {2: "Employee", 3: "Days Worked", 4: "Total Hours",
                     5: "Total Drawings", 6: "In Progress", 7: "Submitted"}.items():
        c = ws2.cell(row=2, column=col, value=hdr)
        c.fill = fill("edf0f2")
        c.font = Font(bold=True, color="4a5568", size=10, name="Arial")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BOTTOM_LINE
    ws2.row_dimensions[2].height = 20

    srow = 3
    for idx, (user_id, user) in enumerate(sorted_users):
        username  = user.get("username", "")
        user_logs = logs.get(user_id, {}) or {}
        if not isinstance(user_logs, dict):
            user_logs = {}

        th = tm = days = 0
        for log_date, entry in user_logs.items():
            if start_date and log_date < start_date: continue
            if end_date   and log_date > end_date:   continue
            hw = entry.get("total_hours", "N/A")
            if hw != "N/A":
                try:
                    h, m = hw.split(":")
                    th += int(h); tm += int(m); days += 1
                except Exception: pass
        extra = tm // 60; rem = tm % 60; total_h = th + extra
        hours_str = f"{total_h}h {rem:02d}m" if days else "—"

        counts = {"in_progress": 0, "submitted": 0, "total": 0}
        for project_id, project in projects_all.items():
            if user_id not in project.get("assigned_users", {}):
                continue
            for drawing in drawings_all.get(project_id, {}).values():
                s = drawing.get("status", "")
                counts["total"] += 1
                if s in counts:
                    counts[s] += 1

        rb = ROW_ALT if idx % 2 else ROW_WHITE
        for col in range(1, SN + 1):
            c = ws2.cell(row=srow, column=col); c.fill = rb; c.border = BOTTOM_LINE

        nc = ws2.cell(row=srow, column=2, value=username)
        nc.fill = rb; nc.border = BOTTOM_LINE
        nc.font = Font(bold=True, color="2d3748", size=10, name="Arial")
        nc.alignment = Alignment(vertical="center")

        def _s(col, val, chip=None, fg="6b7a8d", bold=False):
            c = ws2.cell(row=srow, column=col, value=val)
            c.fill = chip if chip else rb
            c.font = Font(color=fg, size=10, name="Arial", bold=bold)
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = BOTTOM_LINE

        _s(3, days if days else "—")
        _s(4, hours_str)
        _s(5, counts["total"] or "—")
        _s(6, counts["in_progress"] or "—",
           chip=fill("fef9ec") if counts["in_progress"] else None,
           fg="8a6800" if counts["in_progress"] else "9eaab8",
           bold=bool(counts["in_progress"]))
        _s(7, counts["submitted"] or "—",
           chip=fill("ede9fe") if counts["submitted"] else None,
           fg="5b21b6" if counts["submitted"] else "9eaab8",
           bold=bool(counts["submitted"]))

        ws2.row_dimensions[srow].height = 19
        srow += 1

    # ── Save ───────────────────────────────────────────────────────────────────
    date_range = ""
    if start_date and end_date:
        date_range = f"_{start_date}_to_{end_date}"
    elif start_date:
        date_range = f"_from_{start_date}"
    elif end_date:
        date_range = f"_until_{end_date}"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"employee_performance{date_range}_{timestamp}.xlsx"
    full_path = os.path.join(get_reports_directory(), filename)
    wb.save(full_path)
    logger.info(f"Generated employee performance report: {full_path}")
    return full_path