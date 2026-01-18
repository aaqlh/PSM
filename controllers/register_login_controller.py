from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import calendar
from datetime import datetime


from firebase_config import db 
auth = Blueprint("auth", __name__)

# ======================
# HOMEPAGE
# ======================
@auth.route("/", methods=["GET"])
def home_page():
    return render_template("manageregisterlogin/homepage.html")

# ======================
# LOGIN
# ======================
@auth.route("/login", methods=["GET"])
def login_page():
    return render_template("manageregisterlogin/loginpage.html")

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
# REGISTER
# ======================
@auth.route("/register", methods=["GET"])
def show_register():
    return render_template("manageregisterlogin/registerpage.html")

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
    user_ref = db.collection("users").document(username)
    doc = user_ref.get()
    if not doc.exists:
        return redirect(url_for("auth.login_page"))

    user = doc.to_dict() or {}
    salary = float(user.get("salary", 0))
    expenses = user.get("expenses", [])
    commitments = user.get("commitments", [])
    goals = user.get("goals", [])

    # ======================
    # Current month
    # ======================
    today = datetime.now()
    current_month = today.strftime("%Y-%m")

    # CARRY FORWARD LOGIC sama seperti /expense
    months_set = sorted({e["date"][:7] for e in expenses if "date" in e})
    if current_month not in months_set:
        months_set.append(current_month)
        months_set = sorted(months_set)

    carry_balance = 0
    filtered_expenses = []
    total_expense_current = 0
    for month in months_set:
        month_expenses = [e for e in expenses if e.get("date", "").startswith(month)]
        total_expense_month = sum(e.get("amount", 0) for e in month_expenses)
        total_commitment = sum(c.get("amount", 0) for c in commitments)
        remaining_balance = carry_balance + salary - total_commitment - total_expense_month

        if month == current_month:
            filtered_expenses = month_expenses
            current_remaining = remaining_balance
            total_expense_current = total_expense_month

        carry_balance = remaining_balance

    total_goal_amount = sum(g.get("current_amount", 0) for g in goals)
    current_remaining -= total_goal_amount

    # ======================
    # Daily expense dictionary
    # ======================
    # daily_expense[YYYY-MM] = {day: {total, categories}}
    daily_expense = {}
    for e in expenses:
        date_str = e.get("date")
        if not date_str:
            continue
        ym = date_str[:7]
        day = int(date_str.split("-")[2])
        category = e.get("category", "Others")
        amount = float(e.get("amount", 0))
        if ym not in daily_expense:
            daily_expense[ym] = {}
        if day not in daily_expense[ym]:
            daily_expense[ym][day] = {"total":0, "categories":{}}
        daily_expense[ym][day]["total"] += amount
        daily_expense[ym][day]["categories"][category] = daily_expense[ym][day]["categories"].get(category,0)+amount

    # Data untuk bar chart current month
    current_month_daily = daily_expense.get(current_month, {})
    # Untuk JS, kita hantar Object keyed by day: total
    pie_chart_data = {str(day): current_month_daily[day]["total"] for day in current_month_daily}

    return render_template(
        "managedashboard/dashboard.html",
        username=username,
        daily_expense=daily_expense,
        current_month=current_month,
        data={
            "total_expense": round(total_expense_current,2),
            "remaining_balance": round(current_remaining,2),
            "savings": round(total_goal_amount,2)
        },
        pie_chart_data=pie_chart_data
    )


# ======================
# LOGOUT
# ======================
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.home_page"))

# ======================
# RESET PASSWORD
# ======================
@auth.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("manageregisterlogin/reset_password.html")

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
