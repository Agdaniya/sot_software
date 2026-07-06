from datetime import datetime
from core.auth import User


class NotesManager:
    def __init__(self, storage):
        self.storage = storage

    def add_note(self, note_id, project_id, author: User, content):
        if not content.strip():
            raise Exception("Note content cannot be empty")

        data = {
            "note_id": note_id,
            "author_id": author.user_id,
            "author_name": author.username,
            "content": content,
            "created_at": datetime.now().isoformat()
        }

        self.storage.add_note(project_id, note_id, data)
        return data

    def get_notes_for_project(self, project_id):
        return self.storage.get_notes(project_id) or {}
