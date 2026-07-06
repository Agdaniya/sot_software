# setup_superadmin.py
import firebase_admin
from firebase_admin import credentials, auth, db

SERVICE_ACCOUNT_PATH = r"C:\Users\niyaa\OneDrive\Desktop\SOT\firebase_key.json"
DATABASE_URL = "https://sot-staff-tracker-default-rtdb.asia-southeast1.firebasedatabase.app"

SUPERADMIN_EMAIL    = "superadmin@sot.com"   # ← change this
SUPERADMIN_PASSWORD = "Password"               # ← change this
SUPERADMIN_USERNAME = "Super Admin"

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

try:
    user = auth.create_user(email=SUPERADMIN_EMAIL, password=SUPERADMIN_PASSWORD)
    uid = user.uid
    print(f"✅ Auth user created: {uid}")
except auth.EmailAlreadyExistsError:
    user = auth.get_user_by_email(SUPERADMIN_EMAIL)
    uid = user.uid
    print(f"ℹ️  Auth user already exists: {uid}")

db.reference(f"users/{uid}").set({
    "user_id":    uid,
    "username":   SUPERADMIN_USERNAME,
    "email":      SUPERADMIN_EMAIL,
    "role":       "super_admin",
    "first_login": True,
})

print(f"✅ Done! users/{uid} created in database")
print(f"\n🔑 Credentials to give the client:")
print(f"   Email:    {SUPERADMIN_EMAIL}")
print(f"   Password: {SUPERADMIN_PASSWORD}")