from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.services.account_service import register_user
from app.services.exceptions import DuplicateEmailError, InvalidAmountError

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("accounts.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        opening_balance_raw = request.form.get("opening_balance", "0") or "0"

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        try:
            opening_balance = float(opening_balance_raw)
        except ValueError:
            flash("Opening balance must be a number.", "danger")
            return render_template("register.html")

        try:
            user, account = register_user(name, email, password, opening_balance)
            flash(
                f"Account created! Your account number is {account.account_number}.",
                "success",
            )
            return redirect(url_for("auth.login"))
        except DuplicateEmailError:
            flash("That email is already registered.", "danger")
        except InvalidAmountError as e:
            flash(str(e), "danger")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("accounts.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("accounts.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
