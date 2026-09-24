from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.services.account_service import (
    deposit,
    withdraw,
    transfer,
    get_transaction_history,
)
from app.services.exceptions import (
    InvalidAmountError,
    InsufficientFundsError,
    AccountNotFoundError,
    SameAccountTransferError,
)

accounts_bp = Blueprint("accounts", __name__)


def _primary_account():
    return current_user.accounts[0] if current_user.accounts else None


@accounts_bp.route("/")
@accounts_bp.route("/dashboard")
@login_required
def dashboard():
    account = _primary_account()
    return render_template("dashboard.html", account=account)


@accounts_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit_view():
    account = _primary_account()
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", ""))
            deposit(account.id, amount)
            flash(f"Deposited ${amount:.2f} successfully.", "success")
            return redirect(url_for("accounts.dashboard"))
        except (ValueError, InvalidAmountError):
            flash("Please enter a valid positive amount.", "danger")
        except AccountNotFoundError:
            flash("Account not found.", "danger")

    return render_template("deposit.html", account=account)


@accounts_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw_view():
    account = _primary_account()
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", ""))
            withdraw(account.id, amount)
            flash(f"Withdrew ${amount:.2f} successfully.", "success")
            return redirect(url_for("accounts.dashboard"))
        except (ValueError, InvalidAmountError):
            flash("Please enter a valid positive amount.", "danger")
        except InsufficientFundsError:
            flash("Insufficient balance for this withdrawal.", "danger")
        except AccountNotFoundError:
            flash("Account not found.", "danger")

    return render_template("withdraw.html", account=account)


@accounts_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer_view():
    account = _primary_account()
    if request.method == "POST":
        destination = request.form.get("destination", "").strip()
        try:
            amount = float(request.form.get("amount", ""))
            transfer(account.id, destination, amount)
            flash(f"Transferred ${amount:.2f} to account {destination}.", "success")
            return redirect(url_for("accounts.dashboard"))
        except (ValueError, InvalidAmountError):
            flash("Please enter a valid positive amount.", "danger")
        except InsufficientFundsError:
            flash("Insufficient balance for this transfer.", "danger")
        except AccountNotFoundError:
            flash("Destination account not found.", "danger")
        except SameAccountTransferError:
            flash("You cannot transfer to your own account.", "danger")

    return render_template("transfer.html", account=account)


@accounts_bp.route("/transactions")
@login_required
def transactions_view():
    account = _primary_account()
    history = get_transaction_history(account.id) if account else []
    return render_template("transactions.html", account=account, transactions=history)
