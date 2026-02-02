from flask import Blueprint, render_template, session, redirect, url_for
from firebase_admin import firestore
from datetime import datetime
import pytz 

ai = Blueprint("ai", __name__, url_prefix="/ai")
db = firestore.client()

# =====================================================
# FUZZY MEMBERSHIP FUNCTIONS
# =====================================================
def triangular(x, a, b, c):
    if x <= a or x >= c:
        return 0
    elif a < x < b:
        return (x - a) / (b - a)
    elif b <= x < c:
        return (c - x) / (c - b)
    return 0

def trapezoidal(x, a, b, c, d):
    if x <= a or x >= d:
        return 0
    elif b <= x <= c:
        return 1
    elif a < x < b:
        return (x - a) / (b - a)
    elif c < x < d:
        return (d - x) / (d - c)
    return 0

def spending_fuzzy(percent):
    return {
        "Low": trapezoidal(percent, 0, 0, 40, 60),
        "Moderate": triangular(percent, 50, 70, 90),
        "High": trapezoidal(percent, 80, 90, 100, 120)
    }

def balance_fuzzy(ratio):
    return {
        "Safe": trapezoidal(ratio, 25, 30, 100, 100),
        "Warning": triangular(ratio, 10, 17, 25),
        "Critical": trapezoidal(ratio, 0, 0, 5, 10)
    }

# =====================================================
# AI RECOMMENDATION PAGE
# =====================================================
@ai.route("/recommendation")
def ai_page():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return redirect(url_for("auth.login_page"))

    user = user_doc.to_dict()
    salary = float(user.get("salary", 0))
    expenses = user.get("expenses", [])
    existing_plans = user.get("daily_plan", [])

    # ======================
    # FIX TIMEZONE MALAYSIA
    # ======================
    tz = pytz.timezone("Asia/Kuala_Lumpur")
    today = datetime.now(tz).strftime("%Y-%m-%d")
    month_key = today[:7]

    # ======================
    # MONTHLY OVERALL
    # ======================
    total_spent_month = sum(
        e["amount"] for e in expenses if e["date"].startswith(month_key)
    )

    # ✅ FIX: Remaining balance cannot be negative
    remaining_balance = salary - total_spent_month
    remaining_balance = max(0, remaining_balance)

    spent_percent = (total_spent_month / salary * 100) if salary else 0
    balance_ratio = (remaining_balance / salary * 100) if salary else 0

    # ✅ FIX: Clamp fuzzy inputs
    spent_percent = max(0, min(spent_percent, 100))
    balance_ratio = max(0, min(balance_ratio, 100))

    spending_level = spending_fuzzy(spent_percent)
    balance_level = balance_fuzzy(balance_ratio)

    if spending_level["High"] > 0.5 and balance_level["Critical"] > 0.5:
        overall_color = "danger"
        overall_msg = "You are overspending this month."
        overall_advice = "Consider cutting off unnecessary expenses immediately."
    elif spending_level["Moderate"] > 0.5 or balance_level["Warning"] > 0.5:
        overall_color = "warning"
        overall_msg = "Your spending is getting high this month."
        overall_advice = "Be careful with non-essential spending."
    else:
        overall_color = "success"
        overall_msg = "You are managing your money well this month."
        overall_advice = "Your spending is healthy and under control."

    # ======================
    # MONTHLY CATEGORY
    # ======================
    category_monthly = {}
    for e in expenses:
        if e["date"].startswith(month_key):
            category_monthly[e["category"]] = category_monthly.get(e["category"], 0) + e["amount"]

    monthly_categories = []
    for cat, amount in category_monthly.items():
        percent = (amount / salary * 100) if salary else 0
        percent = max(0, min(percent, 100))
        spending_cat = spending_fuzzy(percent)

        if spending_cat["High"] > 0.5 and balance_level["Critical"] > 0.5:
            color = "danger"
            message = f"You are critically overspending on {cat}. Reduce immediately."
        elif spending_cat["Moderate"] > 0.5 or balance_level["Warning"] > 0.5:
            color = "warning"
            message = f"You are spending quite a lot on {cat}. Monitor this category."
        else:
            color = "success"
            message = f"Your spending on {cat} is well balanced."

        monthly_categories.append({
            "category": cat,
            "amount": round(amount, 2),
            "percent": round(percent, 1),
            "color": color,
            "message": message
        })

    # ======================
    # DAILY BUDGET PLAN
    # ======================
    # ✅ FIX: Daily budget based on remaining balance, NOT salary
    daily_budget = remaining_balance / 30 if remaining_balance > 0 else 0

    daily_ratio = {
        "Food": 0.4,
        "Transport": 0.25,
        "Entertainment": 0.2,
        "Others": 0.15
    }

    spent_today = {}
    for e in expenses:
        if e["date"] == today:
            spent_today[e["category"]] = spent_today.get(e["category"], 0) + e["amount"]

    daily_plan = []
    for cat, ratio in daily_ratio.items():
        limit = daily_budget * ratio
        spent = spent_today.get(cat, 0)
        percent = (spent / limit * 100) if limit else 0

        if spent == 0:
            status = "Good"
            color = "success"
            advice = f"You have spent RM0.00 today on {cat}. You are still within a safe range."
        elif percent < 70:
            status = "Good"
            color = "success"
            advice = f"You have spent RM{spent:.2f} on {cat} today."
        elif percent <= 100:
            status = "Warning"
            color = "warning"
            advice = f"You have spent RM{spent:.2f} on {cat} today. Try to limit further spending."
        else:
            status = "Over Budget"
            color = "danger"
            advice = f"You have exceeded today’s {cat} budget."

        daily_plan.append({
            "category": cat,
            "limit": round(limit, 2),
            "spent": round(spent, 2),
            "percent": round(percent, 1),
            "status": status,
            "color": color,
            "advice": advice
        })

    # ======================
    # SAVE DAILY PLAN
    # ======================
    total_daily_plan = round(sum(d["limit"] for d in daily_plan), 2)
    date_exists = any(p["date"] == today for p in existing_plans)

    if not date_exists:
        user_ref.update({
            "daily_plan": firestore.ArrayUnion([
                {
                    "date": today,
                    "amount": total_daily_plan
                }
            ])
        })

    return render_template(
        "airecommendation/ai_recommendation.html",
        salary=salary,
        total_spent_month=round(total_spent_month, 2),
        remaining_balance=round(remaining_balance, 2),
        spent_percent=round(spent_percent, 1),
        overall_color=overall_color,
        overall_msg=overall_msg,
        overall_advice=overall_advice,
        monthly_categories=monthly_categories,
        daily_plan=daily_plan,
        today=today
    )
