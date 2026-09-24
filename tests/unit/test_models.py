import pytest

from app.models import User, Account


class TestUserModel:
    def test_set_password_hashes_value(self, app):
        user = User(name="Alice", email="alice@example.com")
        user.set_password("secret123")
        assert user.password_hash != "secret123"

    def test_check_password_correct(self, app):
        user = User(name="Alice", email="alice@example.com")
        user.set_password("secret123")
        assert user.check_password("secret123") is True

    def test_check_password_incorrect(self, app):
        user = User(name="Alice", email="alice@example.com")
        user.set_password("secret123")
        assert user.check_password("wrong-password") is False

    def test_user_repr_contains_email(self, app):
        user = User(name="Alice", email="alice@example.com")
        assert "alice@example.com" in repr(user)


class TestAccountModel:
    def test_generate_account_number_length(self, app, db):
        number = Account.generate_account_number()
        assert len(number) == 10
        assert number.isdigit()

    def test_generate_account_number_unique(self, app, db):
        acc1 = Account(account_number=Account.generate_account_number(), user_id=1, balance=0)
        db.session.add(acc1)
        db.session.commit()

        number2 = Account.generate_account_number()
        assert number2 != acc1.account_number

    def test_account_repr_contains_balance(self, app):
        account = Account(account_number="1234567890", user_id=1, balance=99.5)
        assert "99.5" in repr(account)
