from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
import uuid

# Initialize Firebase
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

savings_bp = Blueprint("savings", __name__, template_folder="../templates/managesavingsgoal")

# =========================
# LIST SAVINGS GOALS
# =========================
@savings_bp.route("/savings")
def savings():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    goals = user_data.get("goals", [])
    return render_template("SavingsGoalPage.html", goals=goals)


# =========================
# ADD GOAL PAGE
# =========================
@savings_bp.route("/savings/add_goal_page")
def add_goal_page():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))
    return render_template("add_goal.html")


# =========================
# ADD GOAL POST
# =========================
@savings_bp.route("/savings/add_goal", methods=["POST"])
def add_goal():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    name = request.form["name"]
    target_amount = float(request.form["target_amount"])
    current_amount = 0.0

    goal_id = str(uuid.uuid4())

    new_goal = {
        "id": goal_id,
        "name": name,
        "target_amount": target_amount,
        "current_amount": current_amount
    }

    user_ref = db.collection("users").document(session["username"])
    user_doc = user_ref.get()
    goals = user_doc.to_dict().get("goals", [])
    goals.append(new_goal)
    user_ref.update({"goals": goals})

    flash("Goal added successfully", "success")
    return redirect(url_for("savings.savings"))


# =========================
# EDIT GOAL PAGE
# =========================
@savings_bp.route("/savings/edit_goal/<goal_id>")
def edit_goal(goal_id):
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    user_ref = db.collection("users").document(session["username"])
    goals = user_ref.get().to_dict().get("goals", [])
    goal = next((g for g in goals if g["id"] == goal_id), None)
    if not goal:
        flash("Goal not found", "danger")
        return redirect(url_for("savings.savings"))

    return render_template("edit_goal.html", goal=goal)


# =========================
# EDIT GOAL POST
# =========================
@savings_bp.route("/savings/edit_goal/<goal_id>", methods=["POST"])
def update_goal(goal_id):
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    name = request.form["name"]
    target_amount = float(request.form["target_amount"])

    user_ref = db.collection("users").document(session["username"])
    goals = user_ref.get().to_dict().get("goals", [])
    for g in goals:
        if g["id"] == goal_id:
            g["name"] = name
            g["target_amount"] = target_amount
            break
    user_ref.update({"goals": goals})

    flash("Goal updated successfully", "success")
    return redirect(url_for("savings.savings"))


# =========================
# DELETE GOAL
# =========================
@savings_bp.route("/savings/delete_goal/<goal_id>", methods=["POST"])
def delete_goal(goal_id):
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    user_ref = db.collection("users").document(session["username"])
    goals = user_ref.get().to_dict().get("goals", [])
    goals = [g for g in goals if g["id"] != goal_id]
    user_ref.update({"goals": goals})

    flash("Goal deleted", "success")
    return redirect(url_for("savings.savings"))


# =========================
# ADD AMOUNT PAGE
# =========================
@savings_bp.route("/savings/add_amount/<goal_id>", methods=["GET", "POST"])
def add_amount(goal_id):
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    user_ref = db.collection("users").document(session["username"])
    goals = user_ref.get().to_dict().get("goals", [])
    goal = next((g for g in goals if g["id"] == goal_id), None)
    if not goal:
        flash("Goal not found", "danger")
        return redirect(url_for("savings.savings"))

    if request.method == "POST":
        amount = float(request.form["amount"])
        goal["current_amount"] += amount
        user_ref.update({"goals": goals})
        flash("Amount added", "success")
        return redirect(url_for("savings.savings"))

    return render_template("add_amount.html", goal=goal)
