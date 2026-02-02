from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from firebase_admin import firestore
from datetime import datetime

expense_bp = Blueprint("expense", __name__, url_prefix="/expense")
db = firestore.client()

# ======================
# LIST EXPENSES (Current month + carry forward + goals)
# ======================
@expense_bp.route("/", methods=["GET"])
def expenses():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    doc = db.collection("users").document(username).get()
    if not doc.exists:
        flash("User not found", "danger")
        return redirect(url_for("auth.login_page"))

    user = doc.to_dict()
    salary = user.get("salary", 0)
    expenses_list = user.get("expenses", [])
    commitments = user.get("commitments", [])
    goals = user.get("goals", [])

    # ======================
    # MONTH SELECTION
    # ======================
    selected_month = request.args.get("month")
    if not selected_month:
        selected_month = datetime.now().strftime("%Y-%m")

    # ======================
    # GET ALL UNIQUE MONTHS
    # ======================
    months_set = sorted({e["date"][:7] for e in expenses_list if "date" in e})
    if selected_month not in months_set:
        months_set.append(selected_month)
        months_set = sorted(months_set)
    month_labels = {m: datetime.strptime(m, "%Y-%m").strftime("%B %Y") for m in months_set}

    # ======================
    # CARRY FORWARD LOGIC + FILTERED EXPENSES
    # ======================
    months_set_sorted = sorted(months_set)
    carry_balance = 0
    filtered_expenses = []
    filtered_indices = []  # <-- simpan index sebenar dalam DB

    for month in months_set_sorted:
        month_expenses = []
        month_indices = []
        for i, e in enumerate(expenses_list):
            if e.get("date", "").startswith(month):
                month_expenses.append(e)
                month_indices.append(i)

        total_expense = sum(e.get("amount", 0) for e in month_expenses)
        total_commitment = sum(c.get("amount", 0) for c in commitments)
        remaining_balance = carry_balance + salary - total_commitment - total_expense

        if month == selected_month:
            filtered_expenses = month_expenses
            filtered_indices = month_indices
            current_remaining = remaining_balance

        carry_balance = remaining_balance

    # Tolak savings goal
    total_goal_amount = sum(g.get("current_amount", 0) for g in goals)
    current_remaining -= total_goal_amount

    # Format date
    for e in filtered_expenses:
        if "date" in e:
            try:
                dt = datetime.strptime(e["date"], "%Y-%m-%d")
                e["formatted_date"] = dt.strftime("%d/%m/%Y")
            except:
                e["formatted_date"] = e["date"]
        else:
            e["formatted_date"] = ""

    return render_template(
        "manageexpense/expensepage.html",
        username=username,
        salary=salary,
        remaining_balance=current_remaining,
        expenses=filtered_expenses,
        filtered_indices=filtered_indices,  # <-- pass index sebenar
        selected_month=selected_month,
        months_list=months_set,
        month_labels=month_labels,
        total_goal_amount=total_goal_amount,
        goals=goals
    )


# ======================
# ADD / EDIT / DELETE / SALARY ROUTES
# ======================
@expense_bp.route("/add", methods=["GET"])
def add_expense_page():
    categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Others"]
    return render_template("manageexpense/add_expense.html", categories=categories)

@expense_bp.route("/add", methods=["POST"])
def add_expense():
    username = session["username"]
    expense = {
        "expense": request.form["expense"],
        "amount": float(request.form["amount"]),
        "date": request.form["date"],
        "category": request.form["category"]
    }
    user_ref = db.collection("users").document(username)
    user = user_ref.get().to_dict()
    expenses_list = user.get("expenses", [])
    expenses_list.append(expense)
    user_ref.update({"expenses": expenses_list})
    flash("Expense added successfully", "success")
    return redirect(url_for("expense.expenses"))

@expense_bp.route("/edit/<int:index>", methods=["GET", "POST"])
def edit_expense(index):
    username = session["username"]
    user_ref = db.collection("users").document(username)
    user = user_ref.get().to_dict()
    expenses_list = user.get("expenses", [])

    if index >= len(expenses_list):
        flash("Expense not found", "danger")
        return redirect(url_for("expense.expenses"))

    if request.method == "POST":
        expenses_list[index] = {
            "expense": request.form["expense"],
            "amount": float(request.form["amount"]),
            "date": request.form["date"],
            "category": request.form["category"]
        }
        user_ref.update({"expenses": expenses_list})
        flash("Expense updated successfully", "success")
        return redirect(url_for("expense.expenses"))

    categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Others"]
    return render_template(
        "manageexpense/edit_expense.html",
        expense=expenses_list[index],
        index=index,
        categories=categories
    )

@expense_bp.route("/delete/<int:index>", methods=["POST"])
def delete_expense(index):
    username = session["username"]
    user_ref = db.collection("users").document(username)
    user = user_ref.get().to_dict()
    expenses_list = user.get("expenses", [])
    if index < len(expenses_list):
        expenses_list.pop(index)
        user_ref.update({"expenses": expenses_list})
        flash("Expense deleted", "success")
    return redirect(url_for("expense.expenses"))

@expense_bp.route("/salary", methods=["GET"])
def add_salary_page():
    return render_template("manageexpense/add_salary.html")

@expense_bp.route("/salary", methods=["POST"])
def add_salary():
    username = session["username"]
    salary = float(request.form["salary"])
    db.collection("users").document(username).update({"salary": salary})
    flash("Salary updated successfully", "success")
    return redirect(url_for("expense.expenses"))
