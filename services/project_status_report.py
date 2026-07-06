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


# ── Shared palette (matches employee report) ───────────────────────────────────

def fill(hex_color):
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")

CHARCOAL  = fill("2d3748")   # project header band
DARK_BLUE = fill("3d4f63")   # drawing section header
MIST      = fill("f7f9fb")   # meta / summary rows
ROW_WHITE = fill("ffffff")
ROW_ALT   = fill("f4f6f8")

STATUS_FILL = {
    "not_started":     fill("edf0f2"),
    "in_progress":     fill("fef9ec"),
    "completed":       fill("eef3ff"),
    "submitted":       fill("ede9fe"),
    "admin_approved":  fill("edfaf3"),
    "admin_rejected":  fill("fdf0f0"),
    "client_approved": fill("e6f4ef"),
}
STATUS_COLOR = {
    "not_started":     "6b7a8d",
    "in_progress":     "8a6800",
    "completed":       "2557a7",
    "submitted":       "5b21b6",
    "admin_approved":  "1a6b43",
    "admin_rejected":  "9b1c1c",
    "client_approved": "065f46",
}

NO_BORDER   = Border()
BOTTOM_LINE = Border(bottom=Side(style="thin", color="dde3ea"))

NCOLS = 8   # columns A–H


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


def _proj_header(ws, row, name, client):
    _blank(ws, row, bg=CHARCOAL, border=NO_BORDER)
    c = ws.cell(row=row, column=1, value=f"  {name.upper()}   ·   {client}")
    c.fill = CHARCOAL
    c.font = Font(bold=True, color="FFFFFF", size=12, name="Arial")
    c.alignment = Alignment(vertical="center", horizontal="left")
    c.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=NCOLS)
    ws.row_dimensions[row].height = 26


def _meta(ws, row, project_id, employees_text):
    _blank(ws, row, bg=MIST, border=NO_BORDER)
    c1 = ws.cell(row=row, column=1, value=f"  ID: {project_id}")
    c1.fill = MIST; c1.font = Font(color="6b7a8d", size=9, name="Arial", italic=True)
    c1.alignment = Alignment(vertical="center"); c1.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    c2 = ws.cell(row=row, column=4, value=f"Assigned: {employees_text}")
    c2.fill = MIST; c2.font = Font(color="6b7a8d", size=9, name="Arial", italic=True)
    c2.alignment = Alignment(horizontal="right", vertical="center"); c2.border = NO_BORDER
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=NCOLS)
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


def _fmt_date(d):
    if not d: return "—"
    try:
        return datetime.fromisoformat(d).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(d)


# ── Main report ────────────────────────────────────────────────────────────────

def generate_project_status_report():
    """
    Project status report — grouped, collapsible, calm palette.

    Layout per project (drawing rows start hidden):
      ┌─ PROJECT NAME  ·  CLIENT        ← charcoal band, level 0 (always visible)
      │  ID: xxx   Assigned: Alice, Bob ← mist meta,     level 1
      │  Drawings                       ← section header, level 1
      │  [col headers]                  ← level 2, hidden
      │  [drawing rows...]              ← level 2, hidden
      │  X drawings · Y% done · Z paid  ← summary,        level 1
      └─ [spacer]

    Expand with Excel's [+] buttons on the left margin.
    """
    fb = FirebaseClient()
    projects = fb.root.child("projects").get() or {}
    drawings = fb.root.child("drawings").get() or {}
    users    = fb.root.child("users").get()    or {}

    wb = Workbook()
    ws = wb.active
    ws.title = "Project Status"
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.outlinePr.summaryRight = False

    for letter, width in {
        "A": 3,  "B": 28, "C": 18, "D": 16,
        "E": 16, "F": 18, "G": 20, "H": 20
    }.items():
        ws.column_dimensions[letter].width = width

    row = 1

    for project_id, project in projects.items():
        proj_drawings = drawings.get(project_id, {})
        if not isinstance(proj_drawings, dict):
            proj_drawings = {}

        # Employee list
        assigned_users = project.get("assigned_users", {})
        employee_names = []
        for uid in (assigned_users.keys() if isinstance(assigned_users, dict) else []):
            u = users.get(uid, {})
            if u:
                employee_names.append(u.get("username", uid))
        employees_text = ", ".join(employee_names) if employee_names else "None"

        # ── PROJECT HEADER (level 0 — always visible) ────────────────────
        _proj_header(ws, row, project.get("name", ""), project.get("client_name", ""))
        row += 1

        # ── META ROW (level 1) ───────────────────────────────────────────
        _meta(ws, row, project_id, employees_text)
        row += 1

        # ── DRAWINGS SECTION HEADER (level 1) ────────────────────────────
        _sec_hdr(ws, row, "Drawings", DARK_BLUE, outline_level=1)
        row += 1

        # ── COLUMN HEADERS (level 2, hidden) ────────────────────────────
        _col_hdrs(ws, row, {
            2: "Drawing Name", 3: "Status", 4: "Progress",
            5: "Payment", 6: "Payment Date", 7: "Approved Date"
        }, hidden=True)
        row += 1

        # ── DRAWING ROWS (level 2, hidden) ──────────────────────────────
        counts = {k: 0 for k in (
            "not_started", "in_progress", "completed", "submitted",
            "admin_approved", "admin_rejected", "client_approved"
        )}
        paid_count = unpaid_count = 0

        if not proj_drawings:
            _blank(ws, row, bg=ROW_WHITE, border=BOTTOM_LINE)
            c = ws.cell(row=row, column=2, value="No drawings created yet")
            c.font = Font(italic=True, color="9eaab8", size=9, name="Arial")
            c.fill = ROW_WHITE; c.border = BOTTOM_LINE
            c.alignment = Alignment(vertical="center")
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
            ws.row_dimensions[row].height = 16
            ws.row_dimensions[row].outline_level = 2
            ws.row_dimensions[row].hidden = True
            row += 1
        else:
            for idx, (drawing_id, drawing) in enumerate(proj_drawings.items()):
                status           = drawing.get("status", "not_started")
                payment_received = drawing.get("payment_received", False)
                payment_date     = drawing.get("payment_date", "")
                approved_date    = drawing.get("client_approved_date", "")

                if status in counts:
                    counts[status] += 1

                # Progress
                sub_steps = drawing.get("sub_steps", {})
                if sub_steps:
                    done  = sum(1 for s in sub_steps.values() if s.get("completed", False))
                    total = len(sub_steps)
                    progress = f"{done}/{total}  ({int(done / total * 100)}%)"
                else:
                    progress = "—"

                # Payment
                if status in ("admin_approved", "client_approved"):
                    if payment_received:
                        pay_txt = "Paid ✓"; paid_count += 1; paid = True
                    else:
                        pay_txt = "Unpaid ✗"; unpaid_count += 1; paid = False
                else:
                    pay_txt = "—"; paid = None

                rb = ROW_ALT if idx % 2 else ROW_WHITE
                _blank(ws, row, bg=rb, border=BOTTOM_LINE)
                _c(ws, row, 2, drawing.get("name", ""), bg=rb, bold=True)
                _status_chip(ws, row, 3, status)
                _c(ws, row, 4, progress,                bg=rb, ah="center")
                _pay_chip(ws, row, 5, pay_txt, paid=paid if paid is not None else False)
                _c(ws, row, 6, _fmt_date(payment_date), bg=rb, ah="center",
                   fg="6b7a8d", size=9)
                _c(ws, row, 7, _fmt_date(approved_date), bg=rb, ah="center",
                   fg="6b7a8d", size=9)

                ws.row_dimensions[row].height = 17
                ws.row_dimensions[row].outline_level = 2
                ws.row_dimensions[row].hidden = True
                row += 1

        # ── SUMMARY (level 1, always visible) ───────────────────────────
        total_drw   = len(proj_drawings)
        client_done = counts["client_approved"]
        comp_pct    = (f"{round(client_done / total_drw * 100, 1)}%"
                       if total_drw else "0%")
        pay_pct     = (f"{round(paid_count / (paid_count + unpaid_count) * 100, 1)}%"
                       if (paid_count + unpaid_count) else "N/A")

        parts = []
        if total_drw:
            parts.append(f"{total_drw} drawing{'s' if total_drw != 1 else ''}")
        if counts["in_progress"]:
            parts.append(f"{counts['in_progress']} in progress")
        if counts["submitted"]:
            parts.append(f"{counts['submitted']} submitted")
        if client_done:
            parts.append(f"{client_done} client-approved")
        if counts["admin_rejected"]:
            parts.append(f"{counts['admin_rejected']} rejected")
        parts.append(f"completion {comp_pct}")
        if paid_count + unpaid_count:
            parts.append(f"payment {pay_pct}")

        _summary(ws, row, "    ·    ".join(parts), outline_level=1)
        row += 1

        _spacer(ws, row); row += 1

    # ── SUMMARY SHEET ─────────────────────────────────────────────────────────
    ws2 = wb.create_sheet(title="Summary")
    ws2.sheet_view.showGridLines = False
    SN = 7

    for letter, width in {"A": 3, "B": 28, "C": 14, "D": 14,
                          "E": 14, "F": 14, "G": 14}.items():
        ws2.column_dimensions[letter].width = width

    # Title
    for col in range(1, SN + 1):
        c = ws2.cell(row=1, column=col); c.fill = CHARCOAL; c.border = NO_BORDER
    tc = ws2.cell(row=1, column=1, value="  Project Status Summary")
    tc.fill = CHARCOAL; tc.border = NO_BORDER
    tc.font = Font(bold=True, color="FFFFFF", size=12, name="Arial")
    tc.alignment = Alignment(vertical="center", horizontal="left")
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=SN)
    ws2.row_dimensions[1].height = 28

    # Column headers
    for col in range(1, SN + 1):
        c = ws2.cell(row=2, column=col); c.fill = fill("edf0f2"); c.border = BOTTOM_LINE
    for col, hdr in {
        2: "Project", 3: "Client", 4: "Total Drawings",
        5: "Client Approved", 6: "Completion %", 7: "Payment %"
    }.items():
        c = ws2.cell(row=2, column=col, value=hdr)
        c.fill = fill("edf0f2")
        c.font = Font(bold=True, color="4a5568", size=10, name="Arial")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BOTTOM_LINE
    ws2.row_dimensions[2].height = 20

    srow = 3
    for idx, (project_id, project) in enumerate(projects.items()):
        proj_drawings = drawings.get(project_id, {}) or {}
        if not isinstance(proj_drawings, dict):
            proj_drawings = {}

        total_drw   = len(proj_drawings)
        client_done = sum(1 for d in proj_drawings.values()
                          if d.get("status") == "client_approved")
        paid   = sum(1 for d in proj_drawings.values()
                     if d.get("status") in ("admin_approved", "client_approved")
                     and d.get("payment_received", False))
        billable = sum(1 for d in proj_drawings.values()
                       if d.get("status") in ("admin_approved", "client_approved"))

        comp_pct = (f"{round(client_done / total_drw * 100, 1)}%"
                    if total_drw else "0%")
        pay_pct  = (f"{round(paid / billable * 100, 1)}%"
                    if billable else "N/A")

        rb = ROW_ALT if idx % 2 else ROW_WHITE
        for col in range(1, SN + 1):
            c = ws2.cell(row=srow, column=col); c.fill = rb; c.border = BOTTOM_LINE

        ws2.cell(row=srow, column=2, value=project.get("name", "")).font = \
            Font(bold=True, color="2d3748", size=10, name="Arial")
        ws2.cell(row=srow, column=2).fill = rb
        ws2.cell(row=srow, column=2).border = BOTTOM_LINE
        ws2.cell(row=srow, column=2).alignment = Alignment(vertical="center")

        ws2.cell(row=srow, column=3, value=project.get("client_name", "")).font = \
            Font(color="6b7a8d", size=10, name="Arial")
        ws2.cell(row=srow, column=3).fill = rb
        ws2.cell(row=srow, column=3).border = BOTTOM_LINE
        ws2.cell(row=srow, column=3).alignment = Alignment(vertical="center")

        for col, val in [(4, total_drw or "—"), (5, client_done or "—"),
                         (6, comp_pct), (7, pay_pct)]:
            c = ws2.cell(row=srow, column=col, value=val)
            c.fill = rb; c.border = BOTTOM_LINE
            c.font = Font(color="6b7a8d", size=10, name="Arial")
            c.alignment = Alignment(horizontal="center", vertical="center")

        ws2.row_dimensions[srow].height = 19
        srow += 1

    # ── Save ──────────────────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"detailed_project_status_{timestamp}.xlsx"
    full_path = os.path.join(get_reports_directory(), filename)
    wb.save(full_path)
    logger.info(f"Generated project status report: {full_path}")
    return full_path