import firebase_admin
from firebase_admin import credentials

from firebase_config import db

from flask import Flask
from controllers.register_login_controller import auth
from controllers.account_profile_controller import account_profile  # ✅ Betul
from controllers.expense_controller import expense_bp  # 🔹 Import blueprint dari file controller
from controllers.savings_goal_controller import savings_bp
from controllers.ai_recommendation_controller import ai  # bukannya ai_bp

app = Flask(__name__)
app.secret_key = "super-secret-key-123"

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(account_profile)  # ✅ Gunakan nama blueprint yang betul
app.register_blueprint(expense_bp)  # <- register blueprint Expenses
app.register_blueprint(savings_bp)
app.register_blueprint(ai)



if __name__ == "__main__":
    app.run(debug=True)
