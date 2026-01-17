import firebase_admin
from firebase_admin import credentials, firestore

# Path to your JSON key
cred = credentials.Certificate('firebase-key.json')
firebase_admin.initialize_app(cred)

# Firestore database
db = firestore.client()
