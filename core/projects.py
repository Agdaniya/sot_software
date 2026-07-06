from core.auth import SUPER_ADMIN, ADMIN, EMPLOYEE, User


class Project:
    def __init__(self, project_id, name, client_name):
        self.project_id = project_id
        self.name = name
        self.client_name = client_name
        self.assigned_users = set()   # user_ids


class ProjectManager:
    """
    Project creation & assignment logic.
    """

    def __init__(self,storage):
        self.storage = storage

    # -----------------------
    # Permissions
    # -----------------------
    def _can_manage_projects(self, user: User):
        return user.role in [SUPER_ADMIN, ADMIN]

    def _get_project(self, project_id):
        data = self.storage.get_project(project_id)
        if not data:
            raise Exception("Project not found")
        return data

    # -----------------------
    # Project operations
    # -----------------------
    def create_project(self, actor: User, project_id, name, client_name):
        if not self._can_manage_projects(actor):
            raise PermissionError("Not allowed to create project")

        project_data = {
            "project_id": project_id,
            "name": name,
            "client_name": client_name,
            "assigned_users": {}
        }

        self.storage.save_project(project_id, project_data)
        return project_data

    def assign_user(self, actor: User, project_id, user: User):
        if not self._can_manage_projects(actor):
            raise PermissionError("Not allowed to assign users")

        project = self.storage.get_project(project_id)
        if not project:
            raise Exception("Project not found")

        assigned = project.get("assigned_users", {})
        assigned[user.user_id] = True
        project["assigned_users"] = assigned

        self.storage.save_project(project_id, project)


    def get_projects_for_user(self, user: User):
        all_projects = self.storage.get_all_projects()

        if user.role in [SUPER_ADMIN, ADMIN]:
            return list(all_projects.values())

        visible = []
        for project in all_projects.values():
            if project.get("assigned_users", {}).get(user.user_id):
                visible.append(project)

        return visible
