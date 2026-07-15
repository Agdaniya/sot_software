"""
One-time script to create a super_admin user.
Run from inside the sot_software folder:
    python create_superadmin.py

Edit the values below before running.
"""

# ── Configure these ────────────────────────────────────────────────────────────
USERNAME  = "Super Admin"
EMAIL     = "superadmin@test.com"
PASSWORD  = "Admin123!"          # must be at least 6 characters
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os

# Make sure imports resolve from this folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_client import FirebaseClient
import firebase_admin
from firebase_admin import auth as firebase_auth

def main():
    print(f"\nCreating super_admin: {USERNAME} <{EMAIL}>")

    # 1. Init Firebase (FirebaseClient does this)
    fb = FirebaseClient()

    # 2. Check if email already exists in Firebase Auth
    try:
        existing = firebase_auth.get_user_by_email(EMAIL)
        uid = existing.uid
        print(f"  Firebase Auth user already exists (uid: {uid}), reusing.")
    except firebase_auth.UserNotFoundError:
        # Create in Firebase Auth
        new_user = firebase_auth.create_user(
            email=EMAIL,
            password=PASSWORD,
            display_name=USERNAME,
        )
        uid = new_user.uid
        print(f"  Created Firebase Auth user (uid: {uid})")

    # 3. Write profile to Realtime Database
    user_dict = {
        "user_id":        uid,
        "username":       USERNAME,
        "email":          EMAIL.lower(),
        "role":           "super_admin",
        "email_verified": True,
        "first_login":    False,
        "last_login":     None,
    }
    fb.save_user(user_dict)
    print(f"  Saved profile to Realtime Database under /users/{uid}")

    print(f"\nDone! Log in with:")
    print(f"  Email   : {EMAIL}")
    print(f"  Password: {PASSWORD}\n")

if __name__ == "__main__":
    main()
