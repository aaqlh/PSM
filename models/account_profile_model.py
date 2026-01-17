import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase sekali sahaja
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")  # Ganti dengan path sebenar
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ===== GET USER BY USERNAME =====
def get_user_by_username(username):
    users_ref = db.collection("users")
    query = users_ref.where("username", "==", username).get()

    if not query:
        print("User not found in Firebase!")
        return None

    user = query[0].to_dict()
    user["user_id"] = query[0].id

    # Pastikan commitments ada
    if "commitments" not in user:
        user["commitments"] = []

    return user

# ===== UPDATE USER =====
def update_user(user_id, data):
    db.collection("users").document(user_id).update(data)

# ===== DELETE USER =====
def delete_user(user_id):
    db.collection("users").document(user_id).delete()
