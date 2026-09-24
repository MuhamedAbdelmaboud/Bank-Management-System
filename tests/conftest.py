import pytest

from app import create_app, db as _db
from app.services.account_service import register_user


@pytest.fixture
def app():
    flask_app = create_app("config.TestConfig")
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_and_account(app, db):
    user, account = register_user("Test User", "test@example.com", "Password123", 500.0)
    return user, account


def login(client, email="test@example.com", password="Password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
