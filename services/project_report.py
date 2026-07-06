from openpyxl import Workbook
from datetime import datetime
from services.firebase_client import FirebaseClient


def generate_project_status_excel():
    fb = FirebaseClient()
    projects = fb.root.child("projects").get() or {}
    drawings = fb.root.child("drawings").get() or {}

    wb = Workbook()
    ws = wb.active
    ws.title = "Project Status"

    ws.append([
        "Project ID",
        "Project Name",
        "Client",
        "Total Drawings",
        "Submitted",
        "Admin Approved",
        "Client Approved",
        "Completion %"
    ])

    for pid, project in projects.items():
        project_drawings = drawings.get(pid, {})
        total = len(project_drawings)

        submitted = admin_ok = client_ok = 0

        for d in project_drawings.values():
            if d["status"] == "submitted":
                submitted += 1
            elif d["status"] == "admin_approved":
                admin_ok += 1
            elif d["status"] == "client_approved":
                client_ok += 1

        completion = (
            round((client_ok / total) * 100, 2)
            if total > 0 else 0
        )

        ws.append([
            pid,
            project["name"],
            project["client_name"],
            total,
            submitted,
            admin_ok,
            client_ok,
            completion
        ])

    filename = f"project_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    return filename
