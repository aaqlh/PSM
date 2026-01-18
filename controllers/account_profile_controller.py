# controllers/account_profile_controller.py
from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from models.account_profile_model import get_user_by_username, update_user, delete_user

# Blueprint
account_profile = Blueprint("account_profile", __name__)

# ======================
# VIEW PROFILE
# ======================
@account_profile.route("/profile")
def view_profile():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user = get_user_by_username(username)

    if not user:
        # fallback kalau user tak ada di Firebase
        user = {
            "name": "",
            "username": username,
            "email": "",
            "age": "",
            "employment": "",
            "commitments": [],
            "user_id": None
        }

    return render_template("ManageAccountProfile/profilepage.html", user=user)


# ======================
# EDIT PROFILE
# ======================
@account_profile.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user = get_user_by_username(username)

    if not user:
        return "User not found", 404

    if request.method == "POST":
        name = request.form.get("name")
        age = request.form.get("age")
        employment = request.form.get("employment")

        # Ambil commitments dari form
        commitment_names = request.form.getlist("commitment_name[]")
        commitment_values = request.form.getlist("commitment_value[]")

        commitments = []
        for n, v in zip(commitment_names, commitment_values):
            if n.strip() and v.strip():
                commitments.append({"name": n.strip(), "amount": float(v)})

        update_user(user["user_id"], {
            "name": name,
            "age": int(age) if age else "",
            "employment": employment,
            "commitments": commitments
        })

        flash("Profile updated successfully!", "success")
        return redirect(url_for("account_profile.view_profile"))

    return render_template("ManageAccountProfile/EditProfilePage.html", user=user)


# ======================
# DELETE ACCOUNT
# ======================
@account_profile.route("/profile/delete", methods=["POST"])
def delete_account():
    if "username" not in session:
        return redirect(url_for("auth.login_page"))

    username = session["username"]
    user = get_user_by_username(username)

    if not user:
        return "User not found", 404

    delete_user(user["user_id"])
    session.clear()
    flash("Account deleted successfully!", "success")
    return redirect(url_for("auth.login_page"))
