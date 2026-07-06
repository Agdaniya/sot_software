from core.auth import User, SUPER_ADMIN, ADMIN, EMPLOYEE


class PermissionError(Exception):
    pass


class UserManager:
    """
    User & role management.
    ONLY SUPER_ADMIN can manage users.
    """

    def __init__(self, storage):
        self.storage = storage

    # -----------------------
    # Permission helpers
    # -----------------------
    def _require_super_admin(self, actor: User):
        if actor.role != SUPER_ADMIN:
            raise PermissionError("Only Super Admin can perform this action")

    def _get_user(self, user_id):
        data = self.storage.get_user(user_id)
        if not data:
            raise Exception("User not found")

        return User(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            role=data["role"],
            email_verified=data.get("email_verified", False),
            first_login=data.get("first_login", True)
        )

    # -----------------------
    # User management
    # -----------------------
    def create_user(self, actor: User, user_id, username, email, role=EMPLOYEE):
        """Create a new user account"""
        self._require_super_admin(actor)

        # Validate inputs
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        
        if role not in [SUPER_ADMIN, ADMIN, EMPLOYEE]:
            raise ValueError("Invalid role")

        user = User(
            user_id=user_id,
            username=username.strip(),
            email=email.strip().lower(),
            role=role,
            email_verified=False,
            first_login=True
        )

        self.storage.save_user({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "email_verified": user.email_verified,
            "first_login": user.first_login,
            "last_login": None
        })

        return user

    def delete_user(self, actor: User, user_id):
        """
        Delete a user account with CASCADE DELETE
        
        FIX: Now properly cleans up all user references:
        - Removes from project assignments
        - Deletes activity logs
        - Marks notes as from deleted user
        """
        self._require_super_admin(actor)
        
        # Verify user exists
        self._get_user(user_id)
        
        # CASCADE DELETE: Clean up all references to this user
        
        # 1. Remove from all project assignments
        all_projects = self.storage.get_all_projects()
        for project_id, project in all_projects.items():
            assigned_users = project.get("assigned_users", {})
            if user_id in assigned_users:
                self.storage.remove_user_from_project(project_id, user_id)
        
        # 2. Mark all notes by this user as from deleted user
        self.storage.mark_notes_by_deleted_user(user_id)
        
        # 3. Delete activity logs
        self.storage.delete_user_activity_logs(user_id)
        
        # 4. Finally, delete the user record itself
        self.storage.root.child("users").child(user_id).delete()
        
        return True

    def change_role(self, actor: User, user_id, new_role):
        """Change a user's role"""
        self._require_super_admin(actor)

        if new_role not in [SUPER_ADMIN, ADMIN, EMPLOYEE]:
            raise ValueError("Invalid role")

        # Get user data from storage
        user_data = self.storage.get_user(user_id)
        if not user_data:
            raise Exception("User not found")
        
        # Update role
        user_data["role"] = new_role
        
        # Save back to storage
        self.storage.save_user(user_data)
        
        return True

    def force_password_reset(self, actor: User, user_id):
        """Force user to reset password on next login"""
        self._require_super_admin(actor)
        
        # Get user data from storage
        user_data = self.storage.get_user(user_id)
        if not user_data:
            raise Exception("User not found")
        
        # Set first_login flag
        user_data["first_login"] = True
        
        # Save back to storage
        self.storage.save_user(user_data)
        
        return True

    def update_email(self, actor: User, user_id, new_email):
        """Update user's email address"""
        self._require_super_admin(actor)
        
        if not new_email or not new_email.strip():
            raise ValueError("Email cannot be empty")
        
        # Get user data from storage
        user_data = self.storage.get_user(user_id)
        if not user_data:
            raise Exception("User not found")
        
        # Update email and mark as unverified
        user_data["email"] = new_email.strip().lower()
        user_data["email_verified"] = False
        
        # Save back to storage
        self.storage.save_user(user_data)
        
        return True

    def verify_email(self, user_id):
        """Mark user's email as verified"""
        user_data = self.storage.get_user(user_id)
        if not user_data:
            raise Exception("User not found")

        user_data["email_verified"] = True
        self.storage.save_user(user_data)
        
        return True
    
    def get_all_users(self):
        """Get all users in the system"""
        users_data = self.storage.root.child("users").get() or {}
        
        users = []
        for user_id, data in users_data.items():
            users.append(User(
                user_id=data["user_id"],
                username=data["username"],
                email=data["email"],
                role=data["role"],
                email_verified=data.get("email_verified", False),
                first_login=data.get("first_login", True)
            ))
        
        return users
    
    def search_users(self, query):
        """Search users by name or email"""
        all_users = self.get_all_users()
        query_lower = query.lower()
        
        return [
            user for user in all_users
            if query_lower in user.username.lower() or query_lower in user.email.lower()
        ]