import pytest

from tests.conftest import login


class TestRegisterRoute:
    def test_register_page_loads(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_register_success_redirects_to_login(self, client, db):
        resp = client.post(
            "/register",
            data={
                "name": "New User",
                "email": "new@example.com",
                "password": "password1",
                "opening_balance": "100",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"account number" in resp.data.lower()

    def test_register_duplicate_email_shows_error(self, client, db, user_and_account):
        resp = client.post(
            "/register",
            data={
                "name": "Dup",
                "email": "test@example.com",
                "password": "password1",
                "opening_balance": "0",
            },
            follow_redirects=True,
        )
        assert b"already registered" in resp.data.lower()

    def test_register_missing_fields_shows_error(self, client, db):
        resp = client.post(
            "/register",
            data={"name": "", "email": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in resp.data.lower()

    def test_register_invalid_balance_shows_error(self, client, db):
        resp = client.post(
            "/register",
            data={
                "name": "Bad Balance",
                "email": "bad@example.com",
                "password": "password1",
                "opening_balance": "not-a-number",
            },
            follow_redirects=True,
        )
        assert b"must be a number" in resp.data.lower()


class TestLoginRoute:
    def test_login_page_loads(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_login_success(self, client, db, user_and_account):
        resp = login(client)
        assert resp.status_code == 200
        assert b"welcome" in resp.data.lower()

    def test_login_wrong_password(self, client, db, user_and_account):
        resp = login(client, password="wrong-password")
        assert b"invalid email or password" in resp.data.lower()

    def test_login_nonexistent_user(self, client, db):
        resp = login(client, email="nobody@example.com", password="whatever")
        assert b"invalid email or password" in resp.data.lower()

    def test_authenticated_user_redirected_from_login(self, client, db, user_and_account):
        login(client)
        resp = client.get("/login", follow_redirects=True)
        assert b"welcome" in resp.data.lower()


class TestLogoutRoute:
    def test_logout_requires_login(self, client):
        resp = client.get("/logout", follow_redirects=True)
        assert b"login" in resp.data.lower()

    def test_logout_success(self, client, db, user_and_account):
        login(client)
        resp = client.get("/logout", follow_redirects=True)
        assert b"logged out" in resp.data.lower()
