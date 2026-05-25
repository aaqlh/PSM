from flask import Flask
from controllers.register_login_controller import auth
from controllers.account_profile_controller import account_profile
from controllers.expense_controller import expense_bp
from controllers.savings_goal_controller import savings_bp
from controllers.ai_recommendation_controller import ai  # pastikan ini nama blueprint betul
from flask import send_file

# Firebase handled in firebase_config.py
from firebase_config import db  
@app.route('/google123456789.html')
def google_verify():
    return send_file('google123456789.html')
app = Flask(__name__)
app.secret_key = "super-secret-key-123"

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(account_profile)
app.register_blueprint(expense_bp)
app.register_blueprint(savings_bp)
app.register_blueprint(ai)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # Render fix
