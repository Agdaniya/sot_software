from core.auth import SUPER_ADMIN, ADMIN, EMPLOYEE, User


# Drawing statuses
NOT_STARTED = "not_started"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
SUBMITTED = "submitted"
ADMIN_APPROVED = "admin_approved"
ADMIN_REJECTED = "admin_rejected"
CLIENT_APPROVED = "client_approved"


# Updated transitions to support full workflow
VALID_TRANSITIONS = {
    NOT_STARTED: [IN_PROGRESS],
    IN_PROGRESS: [COMPLETED],
    COMPLETED: [SUBMITTED],
    SUBMITTED: [ADMIN_APPROVED, ADMIN_REJECTED],
    ADMIN_REJECTED: [IN_PROGRESS],  # Can go back to in_progress to fix and resubmit
    ADMIN_APPROVED: [CLIENT_APPROVED],  # Can be marked as client approved
    CLIENT_APPROVED: []  # Final state
}


class Drawing:
    def __init__(self, drawing_id, name):
        self.drawing_id = drawing_id
        self.name = name
        self.status = NOT_STARTED
        self.sub_steps = {}  # step_id → completed (bool)

    def add_sub_step(self, step_id, name):
        if step_id in self.sub_steps:
            raise Exception("Sub-step already exists")
        self.sub_steps[step_id] = {
            "name": name,
            "completed": False
        }

    def complete_sub_step(self, step_id):
        if step_id not in self.sub_steps:
            raise Exception("Sub-step not found")
        self.sub_steps[step_id]["completed"] = True

    def all_sub_steps_completed(self):
        return all(step["completed"] for step in self.sub_steps.values())


class DrawingManager:
    def __init__(self, storage):
        self.storage = storage

    def add_drawing(self, project_id, drawing_id, name):
        data = {
            "drawing_id": drawing_id,
            "name": name,
            "status": NOT_STARTED,
            "sub_steps": {}
        }
        self.storage.save_drawing(project_id, drawing_id, data)

    def update_status(self, actor: User, project_id, drawing_id, new_status):
        drawing = self._get_drawing(project_id, drawing_id)

        # Permission checks
        if new_status in [ADMIN_APPROVED, ADMIN_REJECTED] and actor.role not in [ADMIN, SUPER_ADMIN]:
            raise PermissionError("Only Admin can approve/reject")

        if new_status == CLIENT_APPROVED and actor.role not in [ADMIN, SUPER_ADMIN]:
            raise PermissionError("Only Admin can mark client approval")

        # Enforce sub-step completion rule
        if new_status == COMPLETED and drawing.get("sub_steps"):
            all_done = all(
                step["completed"] for step in drawing["sub_steps"].values()
            )
            if not all_done:
                raise Exception(
                    "Cannot mark drawing as COMPLETED until all sub-steps are finished"
                )

        # Validate transition
        if new_status not in VALID_TRANSITIONS[drawing["status"]]:
            raise Exception(
                f"Invalid status change: {drawing['status']} → {new_status}"
            )

        drawing["status"] = new_status
        self.storage.save_drawing(project_id, drawing_id, drawing)

        return new_status

    def _get_drawing(self, project_id, drawing_id):
        data = self.storage.get_drawing(project_id, drawing_id)
        if not data:
            raise Exception("Drawing not found")
        return data