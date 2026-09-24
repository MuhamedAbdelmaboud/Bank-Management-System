from app import db
from app.models import User, Account, Transaction
from app.services.exceptions import (
    InvalidAmountError,
    InsufficientFundsError,
    AccountNotFoundError,
    DuplicateEmailError,
    SameAccountTransferError,
)


def register_user(name, email, password, opening_balance=0.0):
    if User.query.filter_by(email=email).first():
        raise DuplicateEmailError(f"Email {email} is already registered.")

    if opening_balance < 0:
        raise InvalidAmountError("Opening balance cannot be negative.")

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # populate user.id before commit

    account = Account(
        account_number=Account.generate_account_number(),
        user_id=user.id,
        balance=opening_balance,
    )
    db.session.add(account)
    db.session.commit()
    return user, account


def get_account_by_number(account_number):
    account = Account.query.filter_by(account_number=account_number).first()
    if not account:
        raise AccountNotFoundError(f"Account {account_number} not found.")
    return account


def deposit(account_id, amount):
    if amount is None or amount <= 0:
        raise InvalidAmountError("Deposit amount must be positive.")

    account = Account.query.get(account_id)
    if not account:
        raise AccountNotFoundError("Account not found.")

    account.balance += amount
    txn = Transaction(
        account_id=account.id,
        type="deposit",
        amount=amount,
        balance_after=account.balance,
    )
    db.session.add(txn)
    db.session.commit()
    return account


def withdraw(account_id, amount):
    if amount is None or amount <= 0:
        raise InvalidAmountError("Withdrawal amount must be positive.")

    account = Account.query.get(account_id)
    if not account:
        raise AccountNotFoundError("Account not found.")

    if account.balance < amount:
        raise InsufficientFundsError("Insufficient balance for this withdrawal.")

    account.balance -= amount
    txn = Transaction(
        account_id=account.id,
        type="withdraw",
        amount=amount,
        balance_after=account.balance,
    )
    db.session.add(txn)
    db.session.commit()
    return account


def transfer(source_account_id, destination_account_number, amount):
    if amount is None or amount <= 0:
        raise InvalidAmountError("Transfer amount must be positive.")

    source = Account.query.get(source_account_id)
    if not source:
        raise AccountNotFoundError("Source account not found.")

    destination = Account.query.filter_by(account_number=destination_account_number).first()
    if not destination:
        raise AccountNotFoundError("Destination account not found.")

    if source.id == destination.id:
        raise SameAccountTransferError("Cannot transfer to the same account.")

    if source.balance < amount:
        raise InsufficientFundsError("Insufficient balance for this transfer.")

    source.balance -= amount
    destination.balance += amount

    out_txn = Transaction(
        account_id=source.id,
        related_account_id=destination.id,
        type="transfer_out",
        amount=amount,
        balance_after=source.balance,
    )
    in_txn = Transaction(
        account_id=destination.id,
        related_account_id=source.id,
        type="transfer_in",
        amount=amount,
        balance_after=destination.balance,
    )
    db.session.add_all([out_txn, in_txn])
    db.session.commit()
    return source, destination


def get_transaction_history(account_id):
    return (
        Transaction.query.filter_by(account_id=account_id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )
