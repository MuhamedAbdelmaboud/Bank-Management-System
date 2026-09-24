import pytest

from app.services.account_service import (
    register_user,
    deposit,
    withdraw,
    transfer,
    get_account_by_number,
    get_transaction_history,
)
from app.services.exceptions import (
    InvalidAmountError,
    InsufficientFundsError,
    AccountNotFoundError,
    DuplicateEmailError,
    SameAccountTransferError,
)


# ---------------------------------------------------------------------------
# register_user
# ---------------------------------------------------------------------------
class TestRegisterUser:
    def test_creates_user_and_account(self, app, db):
        user, account = register_user("Sara", "sara@example.com", "pw123456", 100.0)
        assert user.id is not None
        assert account.user_id == user.id
        assert account.balance == 100.0

    def test_account_number_generated(self, app, db):
        _, account = register_user("Sara", "sara@example.com", "pw123456", 0)
        assert account.account_number and len(account.account_number) == 10

    def test_duplicate_email_rejected(self, app, db):
        register_user("Sara", "sara@example.com", "pw123456", 0)
        with pytest.raises(DuplicateEmailError):
            register_user("Sara 2", "sara@example.com", "otherpass", 0)

    def test_negative_opening_balance_rejected(self, app, db):
        with pytest.raises(InvalidAmountError):
            register_user("Sara", "sara@example.com", "pw123456", -50)

    @pytest.mark.parametrize("opening_balance", [0, 1, 250.5, 10000])
    def test_various_valid_opening_balances(self, app, db, opening_balance):
        _, account = register_user(
            f"User{opening_balance}", f"user{opening_balance}@example.com", "pw123456", opening_balance
        )
        assert account.balance == opening_balance


# ---------------------------------------------------------------------------
# deposit
# ---------------------------------------------------------------------------
class TestDeposit:
    @pytest.mark.parametrize("amount", [1, 0.01, 100, 9999.99])
    def test_valid_deposit_increases_balance(self, app, db, user_and_account, amount):
        user, account = user_and_account
        starting = account.balance
        deposit(account.id, amount)
        assert account.balance == pytest.approx(starting + amount)

    @pytest.mark.parametrize("amount", [0, -1, -100])
    def test_non_positive_deposit_rejected(self, app, db, user_and_account, amount):
        user, account = user_and_account
        with pytest.raises(InvalidAmountError):
            deposit(account.id, amount)

    def test_deposit_nonexistent_account_raises(self, app, db):
        with pytest.raises(AccountNotFoundError):
            deposit(9999, 100)

    def test_deposit_creates_transaction_record(self, app, db, user_and_account):
        user, account = user_and_account
        deposit(account.id, 50)
        history = get_transaction_history(account.id)
        assert history[0].type == "deposit"
        assert history[0].amount == 50


# ---------------------------------------------------------------------------
# withdraw
# ---------------------------------------------------------------------------
class TestWithdraw:
    @pytest.mark.parametrize("amount", [1, 0.01, 100, 500])
    def test_valid_withdraw_decreases_balance(self, app, db, user_and_account, amount):
        user, account = user_and_account
        starting = account.balance
        withdraw(account.id, amount)
        assert account.balance == pytest.approx(starting - amount)

    @pytest.mark.parametrize("amount", [0, -1, -50])
    def test_non_positive_withdraw_rejected(self, app, db, user_and_account, amount):
        user, account = user_and_account
        with pytest.raises(InvalidAmountError):
            withdraw(account.id, amount)

    def test_withdraw_more_than_balance_rejected(self, app, db, user_and_account):
        user, account = user_and_account
        with pytest.raises(InsufficientFundsError):
            withdraw(account.id, account.balance + 1)

    def test_withdraw_nonexistent_account_raises(self, app, db):
        with pytest.raises(AccountNotFoundError):
            withdraw(9999, 10)

    def test_withdraw_creates_transaction_record(self, app, db, user_and_account):
        user, account = user_and_account
        withdraw(account.id, 25)
        history = get_transaction_history(account.id)
        assert history[0].type == "withdraw"
        assert history[0].amount == 25

    def test_withdraw_exact_balance_allowed(self, app, db, user_and_account):
        user, account = user_and_account
        withdraw(account.id, account.balance)
        assert account.balance == 0


# ---------------------------------------------------------------------------
# transfer
# ---------------------------------------------------------------------------
class TestTransfer:
    def _make_second_account(self, db):
        _, account2 = register_user("Second User", "second@example.com", "pw123456", 200.0)
        return account2

    @pytest.mark.parametrize("amount", [1, 50, 0.5, 200])
    def test_valid_transfer_moves_funds(self, app, db, user_and_account, amount):
        user, source = user_and_account
        destination = self._make_second_account(db)
        source_start, dest_start = source.balance, destination.balance

        transfer(source.id, destination.account_number, amount)

        assert source.balance == pytest.approx(source_start - amount)
        assert destination.balance == pytest.approx(dest_start + amount)

    def test_transfer_insufficient_funds(self, app, db, user_and_account):
        user, source = user_and_account
        destination = self._make_second_account(db)
        with pytest.raises(InsufficientFundsError):
            transfer(source.id, destination.account_number, source.balance + 1)

    def test_transfer_to_nonexistent_account(self, app, db, user_and_account):
        user, source = user_and_account
        with pytest.raises(AccountNotFoundError):
            transfer(source.id, "0000000000", 10)

    def test_transfer_from_nonexistent_account(self, app, db, user_and_account):
        user, source = user_and_account
        destination = self._make_second_account(db)
        with pytest.raises(AccountNotFoundError):
            transfer(999999, destination.account_number, 10)

    def test_transfer_to_same_account_rejected(self, app, db, user_and_account):
        user, source = user_and_account
        with pytest.raises(SameAccountTransferError):
            transfer(source.id, source.account_number, 10)

    @pytest.mark.parametrize("amount", [0, -1, -20])
    def test_non_positive_transfer_rejected(self, app, db, user_and_account, amount):
        user, source = user_and_account
        destination = self._make_second_account(db)
        with pytest.raises(InvalidAmountError):
            transfer(source.id, destination.account_number, amount)

    def test_transfer_creates_two_transaction_records(self, app, db, user_and_account):
        user, source = user_and_account
        destination = self._make_second_account(db)
        transfer(source.id, destination.account_number, 30)

        source_history = get_transaction_history(source.id)
        dest_history = get_transaction_history(destination.id)

        assert source_history[0].type == "transfer_out"
        assert dest_history[0].type == "transfer_in"
        assert source_history[0].amount == 30
        assert dest_history[0].amount == 30


# ---------------------------------------------------------------------------
# lookups
# ---------------------------------------------------------------------------
class TestLookups:
    def test_get_account_by_number_found(self, app, db, user_and_account):
        user, account = user_and_account
        result = get_account_by_number(account.account_number)
        assert result.id == account.id

    def test_get_account_by_number_not_found(self, app, db):
        with pytest.raises(AccountNotFoundError):
            get_account_by_number("nonexistent")

    def test_get_transaction_history_empty_for_new_account(self, app, db, user_and_account):
        user, account = user_and_account
        assert get_transaction_history(account.id) == []

    def test_get_transaction_history_ordered_most_recent_first(self, app, db, user_and_account):
        user, account = user_and_account
        deposit(account.id, 10)
        deposit(account.id, 20)
        history = get_transaction_history(account.id)
        assert history[0].amount == 20
        assert history[1].amount == 10
