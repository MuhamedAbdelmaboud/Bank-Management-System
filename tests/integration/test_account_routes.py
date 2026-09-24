import pytest

from tests.conftest import login


@pytest.mark.parametrize("endpoint", ["/dashboard", "/deposit", "/withdraw", "/transfer", "/transactions"])
def test_protected_routes_require_login(client, endpoint):
    resp = client.get(endpoint, follow_redirects=True)
    assert b"login" in resp.data.lower()


class TestDashboard:
    def test_dashboard_shows_balance(self, client, db, user_and_account):
        login(client)
        resp = client.get("/dashboard")
        assert b"500.00" in resp.data


class TestDepositRoute:
    def test_deposit_page_loads(self, client, db, user_and_account):
        login(client)
        resp = client.get("/deposit")
        assert resp.status_code == 200

    def test_valid_deposit_updates_balance(self, client, db, user_and_account):
        login(client)
        client.post("/deposit", data={"amount": "100"}, follow_redirects=True)
        resp = client.get("/dashboard")
        assert b"600.00" in resp.data

    def test_negative_deposit_rejected(self, client, db, user_and_account):
        login(client)
        resp = client.post("/deposit", data={"amount": "-10"}, follow_redirects=True)
        assert b"valid positive amount" in resp.data.lower()

    def test_non_numeric_deposit_rejected(self, client, db, user_and_account):
        login(client)
        resp = client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        assert b"valid positive amount" in resp.data.lower()


class TestWithdrawRoute:
    def test_withdraw_page_loads(self, client, db, user_and_account):
        login(client)
        resp = client.get("/withdraw")
        assert resp.status_code == 200

    def test_valid_withdraw_updates_balance(self, client, db, user_and_account):
        login(client)
        client.post("/withdraw", data={"amount": "100"}, follow_redirects=True)
        resp = client.get("/dashboard")
        assert b"400.00" in resp.data

    def test_withdraw_insufficient_funds(self, client, db, user_and_account):
        login(client)
        resp = client.post("/withdraw", data={"amount": "999999"}, follow_redirects=True)
        assert b"insufficient balance" in resp.data.lower()

    def test_withdraw_negative_rejected(self, client, db, user_and_account):
        login(client)
        resp = client.post("/withdraw", data={"amount": "-5"}, follow_redirects=True)
        assert b"valid positive amount" in resp.data.lower()


class TestTransferRoute:
    def test_transfer_page_loads(self, client, db, user_and_account):
        login(client)
        resp = client.get("/transfer")
        assert resp.status_code == 200

    def test_valid_transfer_updates_balances(self, client, db, user_and_account, app):
        from app.services.account_service import register_user

        _, destination = register_user("Second User", "second@example.com", "password1", 50.0)
        _, source = user_and_account

        login(client)
        resp = client.post(
            "/transfer",
            data={"destination": destination.account_number, "amount": "50"},
            follow_redirects=True,
        )
        assert b"transferred" in resp.data.lower()

        dashboard = client.get("/dashboard")
        assert b"450.00" in dashboard.data

    def test_transfer_to_self_rejected(self, client, db, user_and_account):
        user, account = user_and_account
        login(client)
        resp = client.post(
            "/transfer",
            data={"destination": account.account_number, "amount": "10"},
            follow_redirects=True,
        )
        assert b"cannot transfer to your own account" in resp.data.lower()

    def test_transfer_to_unknown_account_rejected(self, client, db, user_and_account):
        login(client)
        resp = client.post(
            "/transfer",
            data={"destination": "0000000000", "amount": "10"},
            follow_redirects=True,
        )
        assert b"destination account not found" in resp.data.lower()

    def test_transfer_insufficient_funds(self, client, db, user_and_account):
        login(client)
        resp = client.post(
            "/transfer",
            data={"destination": "0000000001", "amount": "999999"},
            follow_redirects=True,
        )
        assert resp.status_code == 200


class TestTransactionsRoute:
    def test_transactions_page_loads_empty(self, client, db, user_and_account):
        login(client)
        resp = client.get("/transactions")
        assert b"no transactions yet" in resp.data.lower()

    def test_transactions_page_shows_history(self, client, db, user_and_account):
        login(client)
        client.post("/deposit", data={"amount": "20"}, follow_redirects=True)
        resp = client.get("/transactions")
        assert b"deposit" in resp.data.lower()
