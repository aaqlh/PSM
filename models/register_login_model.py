from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore

# ===== FIREBASE INIT =====
cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

auth = Blueprint("auth", __name__)

# ======================
# LOGIN PAGE
# ======================
@auth.route("/", methods=["GET"])
@auth.route("/login", methods=["GET"])
def login_page():
    return render_template("manageregisterlogin/loginpage.html")

# ======================
# HANDLE LOGIN
# ======================
@auth.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")

    doc = db.collection("users").document(username).get()
    if not doc.exists or doc.to_dict().get("password") != password:
        flash("Invalid username or password!", "danger")
        return redirect(url_for("auth.login_page"))

    session["username"] = username
    return redirect(url_for("auth.dashboard"))

# ======================
# REGISTER PAGE
# ======================
@auth.route("/register", methods=["GET"])
def show_register():
    return render_template("manageregisterlogin/registerpage.html")

# ======================
# HANDLE REGISTER
# ======================
@auth.route("/register", methods=["POST"])
def do_register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    employment = request.form.get("employment_status")
    commitments_name = request.form.getlist("commitment_name[]")
    commitments_value = request.form.getlist("commitment_value[]")

    commitments = []
    for name, value in zip(commitments_name, commitments_value):
        if name and value:
            commitments.append({"name": name, "amount": float(value)})

    db.collection("users").document(username).set({
        "username": username,
        "email": email,
        "password": password,
        "age": age,
        "employment": employment,
        "commitments": commitments
    })

    session["username"] = username
    return redirect(url_for("auth.dashboard"))

# ======================
# DASHBOARD
# ======================
@auth.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user_ref = db.collection("users").document(username).get()
    if not user_ref.exists:
        flash("User not found!", "danger")
        return redirect(url_for("auth.login_page"))

    user = user_ref.to_dict()
    return render_template("managedashboard/dashboard.html", username=username, user=user)

# ======================
# LOGOUT
# ======================
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))

# ======================
# RESET PASSWORD PAGE
# ======================
@auth.route("/forgot-password", methods=["GET"])
def forgot_password():
    """
    Paparkan form untuk user reset password baru
    """
    return render_template("manageregisterlogin/reset_password.html")

# ======================
# HANDLE RESET PASSWORD
# ======================
@auth.route("/forgot-password", methods=["POST"])
def do_reset_password():
    username = request.form.get("username")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if new_password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for("auth.forgot_password"))

    doc = db.collection("users").document(username).get()
    if not doc.exists:
        flash("User not found!", "danger")
        return redirect(url_for("auth.forgot_password"))

    db.collection("users").document(username).update({"password": new_password})
    flash("Password successfully updated!", "success")
    return redirect(url_for("auth.login_page"))
