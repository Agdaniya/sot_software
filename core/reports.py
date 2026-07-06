import pandas as pd
from datetime import datetime


class ReportManager:
    def __init__(self, storage):
        self.storage = storage

    def generate_employee_performance(self):
        users = self.storage.root.child("users").get() or {}

        data = []
        for user_id, user in users.items():
            data.append({
                "User ID": user_id,
                "Username": user.get("username"),
                "Role": user.get("role"),
                "Email": user.get("email"),
                "Last Login": user.get("last_login")
            })

        df = pd.DataFrame(data)
        filename = f"employee_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        return filename

    def generate_project_status(self):
        projects = self.storage.root.child("projects").get() or {}

        data = []
        for pid, project in projects.items():
            data.append({
                "Project ID": pid,
                "Project Name": project.get("name"),
                "Client": project.get("client_name"),
                "Assigned Users": ", ".join(project.get("assigned_users", {}).keys())
            })

        df = pd.DataFrame(data)
        filename = f"project_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        return filename
