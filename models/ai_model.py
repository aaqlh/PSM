# models/ai_model.py
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase sekali sahaja
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def get_user_data(username):
    """Fetch user data dari Firebase Firestore"""
    doc = db.collection("users").document(username).get()
    if doc.exists:
        return doc.to_dict()
    return None

def ai_recommendation(expenses, salary, goals):
    """
    AI recommendation untuk budget plan personalized
    expenses: list of dicts {expense, amount, category, date}
    salary: total user salary
    goals: list of dicts {current_amount, target_amount, name}
    return: list of dicts {category, budget, spent, status, suggestion}
    """

    # Step 1: Tentukan budget plan per category (dynamic based on salary & savings goals)
    total_goal_remaining = sum(g['target_amount'] - g['current_amount'] for g in goals)
    saving_ratio = min(total_goal_remaining / salary, 0.3)  # max 30% salary untuk saving

    # Dynamic allocation: prioritize savings, rest untuk spending
    remaining_salary = salary * (1 - saving_ratio)
    budget_plan = {
        "Food": remaining_salary * 0.3,
        "Transport": remaining_salary * 0.1,
        "Shopping": remaining_salary * 0.15,
        "Entertainment": remaining_salary * 0.1,
        "Bills": remaining_salary * 0.2,
        "Others": remaining_salary * 0.15
    }

    # Step 2: Hitung total spent per category
    spent_per_category = {cat: 0 for cat in budget_plan.keys()}
    for e in expenses:
        cat = e.get("category", "Others")
        amt = e.get("amount", 0)
        if cat in spent_per_category:
            spent_per_category[cat] += amt
        else:
            spent_per_category["Others"] += amt

    # Step 3: Tentukan status & suggestion
    results = []
    for cat, budget in budget_plan.items():
        spent = spent_per_category.get(cat, 0)
        if spent <= budget * 0.9:
            status = "Normal"
            suggestion = "Good job! Keep spending in check."
        elif spent <= budget:
            status = "Warning"
            suggestion = "Almost reaching your budget. Monitor spending."
        else:
            status = "Critical"
            suggestion = "You have exceeded your budget! Reduce expenses."

        results.append({
            "category": cat,
            "budget": round(budget, 2),
            "spent": round(spent, 2),
            "status": status,
            "suggestion": suggestion
        })

    return results
