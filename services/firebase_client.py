import firebase_admin
from firebase_admin import credentials, db
from datetime import date, datetime, timedelta
import os
import sys


class FirebaseClient:
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(self._get_firebase_key_path())
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://sot-staff-tracker-default-rtdb.asia-southeast1.firebasedatabase.app/"
            })

        self.root = db.reference("/")

    def _get_firebase_key_path(self):
        """
        Resolve firebase_key.json safely for:
        - local development
        - bundled exe (PyInstaller)
        
        FIX: Enhanced path resolution with multiple fallback locations
        """
        # Possible locations to check
        possible_paths = []
        
        if getattr(sys, "frozen", False):
            # Running as exe - PyInstaller extracts to _MEIPASS temp directory
            base_path = sys._MEIPASS
            possible_paths.append(os.path.join(base_path, "firebase_key.json"))
            
            # Also check next to the executable itself
            exe_dir = os.path.dirname(sys.executable)
            possible_paths.append(os.path.join(exe_dir, "firebase_key.json"))
        else:
            # Running from source
            # Check in the same directory as this file
            base_path = os.path.dirname(os.path.abspath(__file__))
            possible_paths.append(os.path.join(base_path, "firebase_key.json"))
            
            # Check one level up (project root)
            possible_paths.append(os.path.join(base_path, "..", "firebase_key.json"))
            
            # Check in current working directory
            possible_paths.append(os.path.join(os.getcwd(), "firebase_key.json"))
        
        # Try each path and return the first one that exists
        for path in possible_paths:
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                print(f"Found firebase_key.json at: {normalized_path}")
                return normalized_path
        
        # If none found, show helpful error message
        error_msg = (
            "ERROR: firebase_key.json not found!\n\n"
            "Searched in the following locations:\n"
        )
        for path in possible_paths:
            error_msg += f"  - {os.path.normpath(path)}\n"
        
        error_msg += (
            "\nPlease ensure firebase_key.json is in one of these locations:\n"
            "1. Next to the executable file (for .exe)\n"
            "2. In the project root directory (for development)\n"
        )
        
        raise FileNotFoundError(error_msg)

    # -----------------------
    # USERS
    # -----------------------
    def save_user(self, user_dict):
        user_id = user_dict["user_id"]
        self.root.child("users").child(user_id).set(user_dict)

    def get_user(self, user_id):
        return self.root.child("users").child(user_id).get()
    
    def get_all_users(self):
        """FIX: Added method to get all users"""
        return self.root.child("users").get() or {}

    # -----------------------
    # PROJECTS
    # -----------------------
    def save_project(self, project_id, data):
        self.root.child("projects").child(project_id).set(data)

    def get_project(self, project_id):
        return self.root.child("projects").child(project_id).get()

    def get_all_projects(self):
        return self.root.child("projects").get() or {}
    
    def remove_user_from_project(self, project_id, user_id):
        """FIX: Remove a user from a project's assigned_users"""
        project = self.get_project(project_id)
        if project and "assigned_users" in project:
            assigned = project.get("assigned_users", {})
            if user_id in assigned:
                del assigned[user_id]
                project["assigned_users"] = assigned
                self.save_project(project_id, project)

    # -----------------------
    # DRAWINGS
    # -----------------------
    def save_drawing(self, project_id, drawing_id, data):
        self.root.child("drawings").child(project_id).child(drawing_id).set(data)

    def get_drawing(self, project_id, drawing_id):
        return (
            self.root
            .child("drawings")
            .child(project_id)
            .child(drawing_id)
            .get()
        )

    def get_drawings_for_project(self, project_id):
        return self.root.child("drawings").child(project_id).get() or {}

    # -----------------------
    # CLIENT APPROVAL & PAYMENT TRACKING
    # -----------------------
    def mark_drawing_client_approved(self, project_id, drawing_id):
        self.root.child("drawings").child(project_id).child(drawing_id).update({
            "status": "client_approved",
            "client_approved_date": datetime.now().isoformat()
        })

    def mark_drawing_paid(self, project_id, drawing_id, paid_status=True):
        self.root.child("drawings").child(project_id).child(drawing_id).update({
            "payment_received": paid_status,
            "payment_date": datetime.now().isoformat() if paid_status else None
        })

    def get_drawing_payment_status(self, project_id, drawing_id):
        drawing = self.get_drawing(project_id, drawing_id)
        if drawing:
            return drawing.get("payment_received", False)
        return False

    # -----------------------
    # NOTES
    # -----------------------
    def add_note(self, project_id, note_id, data):
        self.root.child("notes").child(project_id).child(note_id).set(data)

    def get_notes(self, project_id):
        return self.root.child("notes").child(project_id).get()
    
    def mark_notes_by_deleted_user(self, user_id):
        """FIX: Mark all notes by a deleted user"""
        all_notes = self.root.child("notes").get() or {}
        for project_id, project_notes in all_notes.items():
            if isinstance(project_notes, dict):
                for note_id, note in project_notes.items():
                    if note.get("author_id") == user_id:
                        # Mark the note as from a deleted user
                        self.root.child("notes").child(project_id).child(note_id).update({
                            "author_deleted": True
                        })

    # -----------------------
    # ACTIVITY LOGS
    # -----------------------
    def record_login_time(self, user_id):
        """
        Record the FIRST login time of the day.
        """
        today = date.today().isoformat()
        now   = datetime.now().strftime("%H:%M:%S")

        user_day_ref = self.root.child("activity_logs").child(user_id).child(today)
        day_data     = user_day_ref.get() or {}

        # Only record login_time once (the first login of the day)
        if not day_data.get("login_time"):
            user_day_ref.update({"login_time": now})

    def record_logout_time(self, user_id):
        """
        Record the LAST logout time of the day.
        Total hours = last logout minus first login (gaps included).
        """
        today = date.today().isoformat()
        now   = datetime.now()

        user_day_ref = self.root.child("activity_logs").child(user_id).child(today)
        day_data     = user_day_ref.get() or {}

        login_time = day_data.get("login_time")
        if not login_time:
            return

        login_dt = datetime.strptime(login_time, "%H:%M:%S").replace(
            year=now.year, month=now.month, day=now.day
        )

        # Handle midnight crossover
        if now < login_dt:
            now = now + timedelta(days=1)

        delta  = now - login_dt
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        mins   = remainder // 60

        user_day_ref.update({
            "logout_time": now.strftime("%H:%M:%S"),
            "total_hours": f"{hours}:{mins:02d}",
        })
    
    def delete_user_activity_logs(self, user_id):
        """FIX: Delete all activity logs for a user"""
        self.root.child("activity_logs").child(user_id).delete()

    # -----------------------
    # PROJECT TEMPLATE
    # -----------------------
    def get_project_template(self):
        return self.root.child("project_template").get() or {}

    def save_template_drawing(self, drawing_id, data):
        self.root.child("project_template").child(drawing_id).set(data)

    def add_template_substep(self, drawing_id, step_id, data):
        self.root.child("project_template").child(drawing_id).child("sub_steps").child(step_id).set(data)

    def delete_template_drawing(self, drawing_id):
        self.root.child("project_template").child(drawing_id).delete()

    def delete_template_substep(self, drawing_id, step_id):
        self.root.child("project_template").child(drawing_id).child("sub_steps").child(step_id).delete()

    # -----------------------
    # TASKS
    # -----------------------
    def assign_task(self, task_id, data):
        """Save a task. data must include assigned_to, title, description, due_date, created_by, status."""
        self.root.child("tasks").child(task_id).set(data)

    def get_task(self, task_id):
        return self.root.child("tasks").child(task_id).get()

    def get_all_tasks(self):
        return self.root.child("tasks").get() or {}

    def get_tasks_for_user(self, user_id):
        all_tasks = self.get_all_tasks()
        return {tid: t for tid, t in all_tasks.items() if t.get("assigned_to") == user_id}

    def update_task_status(self, task_id, status):
        self.root.child("tasks").child(task_id).update({"status": status})

    def delete_task(self, task_id):
        self.root.child("tasks").child(task_id).delete()

    def update_project_assignments(self, project_id, user_ids):
        self.root.child("projects").child(project_id).child("assigned_users").set(user_ids)

    def create_project_drawings_from_template(self, project_id):
        template = self.get_project_template()

        for drawing_id, drawing in template.items():
            sub_steps = {}
            for sid, step in drawing.get("sub_steps", {}).items():
                sub_steps[sid] = {
                    "name": step["name"],
                    "completed": False
                }

            self.root.child("drawings").child(project_id).child(drawing_id).set({
                "name": drawing["name"],
                "status": "not_started",
                "sub_steps": sub_steps,
                "payment_received": False,
                "payment_date": None
            })