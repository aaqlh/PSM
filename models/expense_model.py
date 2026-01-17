import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialization
cred = credentials.Certificate("C:/Users/ainaa/Downloads/PSM/firebase_service_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_user_data(username):
    """Fetch user data from Firebase and return as dict"""
    doc = db.collection("users").document(username).get()
    if doc.exists:
        return doc.to_dict()
    return None


def ai_recommendation(expenses, salary):
    """
    Simple AI recommendation based on fixed category budgets.
    expenses: list of dicts with keys: expense, amount, category, date
    salary: user's total salary
    returns: list of dicts with keys: category, budget, spent, status, suggestion
    """

    # Budget plan per category
    budget_plan = {
        "Food": 0.3 * salary,
        "Transport": 0.1 * salary,
        "Shopping": 0.15 * salary,
        "Entertainment": 0.1 * salary,
        "Bills": 0.2 * salary,
        "Others": 0.15 * salary
    }

    # Calculate spent per category
    spent_per_category = {cat: 0 for cat in budget_plan.keys()}

    for e in expenses:
        cat = e.get("category", "Others")
        amt = e.get("amount", 0)
        if cat in spent_per_category:
            spent_per_category[cat] += amt
        else:
            spent_per_category["Others"] += amt

    # Generate recommendation with status and suggestion
    results = []
    for cat, budget in budget_plan.items():
        spent = spent_per_category.get(cat, 0)
        if spent <= budget * 0.9:
            status = "Normal"
            suggestion = "Good job! Keep your spending in check."
        elif spent <= budget:
            status = "Warning"
            suggestion = "Almost reaching your budget. Monitor spending."
        else:
            status = "Over"
            suggestion = "You have exceeded your budget! Consider reducing expenses."

        results.append({
            "category": cat,
            "budget": round(budget, 2),
            "spent": round(spent, 2),
            "status": status,
            "suggestion": suggestion
        })

    return results
