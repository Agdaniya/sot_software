import re


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email(email):
        """
        Validate email format
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not email or not email.strip():
            return False, "Email cannot be empty"
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_username(username):
        """
        Validate username
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not username or not username.strip():
            return False, "Username cannot be empty"
        
        if len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 50:
            return False, "Username too long (max 50 characters)"
        
        if not re.match(r'^[a-zA-Z0-9_\s]+$', username):
            return False, "Username can only contain letters, numbers, spaces, and underscores"
        
        return True, ""
    
    @staticmethod
    def validate_project_name(name):
        """
        Validate project name
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not name or not name.strip():
            return False, "Project name cannot be empty"
        
        if len(name) > 100:
            return False, "Project name too long (max 100 characters)"
        
        return True, ""
    
    @staticmethod
    def validate_password(password):
        """
        Validate password strength
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        return True, ""
    
    @staticmethod
    def validate_not_empty(value, field_name="Field"):
        """
        Generic validation for non-empty fields
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not value or not str(value).strip():
            return False, f"{field_name} cannot be empty"
        
        return True, ""