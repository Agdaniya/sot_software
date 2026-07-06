from openpyxl import Workbook
from datetime import datetime
from services.firebase_client import FirebaseClient


def generate_employee_performance_excel(start_date, end_date):
    fb = FirebaseClient()
    users = fb.root.child("users").get() or {}
    logs = fb.root.child("activity_logs").get() or {}

    wb = Workbook()
    ws = wb.active
    ws.title = "Employee Performance"

    ws.append([
        "Employee Name",
        "Date",
        "Login Time",
        "Logout Time",
        "Hours Worked"
    ])

    for user_id, user in users.items():
        user_logs = logs.get(user_id, {})

        for date, entry in user_logs.items():
            if not (start_date <= date <= end_date):
                continue

            login = entry.get("login_time")
            logout = entry.get("logout_time")

            if not login or not logout:
                continue

            login_dt = datetime.fromisoformat(login)
            logout_dt = datetime.fromisoformat(logout)
            hours = round(
                (logout_dt - login_dt).total_seconds() / 3600, 2
            )

            ws.append([
                user["username"],
                date,
                login_dt.strftime("%H:%M:%S"),
                logout_dt.strftime("%H:%M:%S"),
                hours
            ])

    filename = f"employee_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    return filename
