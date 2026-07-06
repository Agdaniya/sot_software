from datetime import datetime

# Role constants
SUPER_ADMIN = "super_admin"
ADMIN = "admin"
EMPLOYEE = "employee"



class User:
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        role: str,
        email_verified: bool = False,
        first_login: bool = True
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.email_verified = email_verified
        self.first_login = first_login
        self.last_login = None

    def record_login(self):
        self.last_login = datetime.now()


def login(user: User):
    """
    Core login logic.
    UI / Firebase will call this.
    """
    if not user.email_verified:
        raise Exception("Email not verified")

    user.record_login()

    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "first_login": user.first_login,
        "last_login": user.last_login
    }
