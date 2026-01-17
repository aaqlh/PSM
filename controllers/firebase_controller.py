from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

# Blueprint
auth = Blueprint("auth", __name__)

# In-memory "database" for demo purposes
USERS_DB = {}  # {username: user_dict}

# =========================
# REGISTER PAGE
# =========================
@auth.route("/register", methods=["GET"])
def show_register():
    return render_template("manageregisterlogin/registerpage.html")


# =========================
# HANDLE REGISTER
# =========================
@auth.route("/register", methods=["POST"])
def do_register():
    name = request.form.get("name")
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    employment = request.form.get("employment_status")

    # Get commitments from form
    commitment_names = request.form.getlist("commitment_name[]")
    commitment_values = request.form.getlist("commitment_value[]")
    commitments = [{"name": n, "value": float(v)} for n, v in zip(commitment_names, commitment_values)]

    # Check if username already exists
    if username in USERS_DB:
        flash("Username already exists", "error")
        return redirect(url_for("auth.show_register"))

    # Save user to "database"
    USERS_DB[username] = {
        "user_id": len(USERS_DB) + 1,
        "name": name,
        "username": username,
        "email": email,
        "password_hash": generate_password_hash(password),
        "age": age,
        "employment": employment,
        "commitments": commitments,
        # Initial financial data for dashboard
        "remaining_balance": 5000,
        "total_expense": 1200,
        "savings": 3000,
        "spending_categories": {
            "Food": 500,
            "Transport": 300,
            "Shopping": 200
        },
        "chart_data": {
            "months": ["Jan", "Feb", "Mar", "Apr"],
            "expenses": [400, 600, 500, 700]
        }
    }

    # Auto-login after registration
    session["user_id"] = USERS_DB[username]["user_id"]
    session["username"] = username
    flash("Registration successful! 🎉", "success")
    return redirect(url_for("auth.dashboard"))


# =========================
# LOGIN PAGE
# =========================
@auth.route("/login", methods=["GET"])
def login_page():
    return render_template("manageregisterlogin/loginpage.html")


# =========================
# HANDLE LOGIN
# =========================
@auth.route("/do_login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = USERS_DB.get(username)
    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        flash("Login successful 🎉", "success")
        return redirect(url_for("auth.dashboard"))
    else:
        flash("Incorrect username or password", "error")
        return redirect(url_for("auth.login_page"))


# =========================
# DASHBOARD
# =========================
@auth.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    username = session.get("username")
    user = USERS_DB.get(username)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("auth.login_page"))

    # Pass data to template
    data = {
        "remaining_balance": user.get("remaining_balance", 0),
        "total_expense": user.get("total_expense", 0),
        "savings": user.get("savings", 0),
        "commitments": user.get("commitments", []),
        "spending_categories": user.get("spending_categories", {}),
        "chart_data": user.get("chart_data", {"months": [], "expenses": []})
    }

    return render_template("managedashboard/dashboard.html", username=username, data=data)


# =========================
# LOGOUT
# =========================
@auth.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login_page"))
