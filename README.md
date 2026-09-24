# Bank Management System

A full-stack banking web application built with **Flask**, **SQLAlchemy**, and **SQLite**,
featuring account creation, authentication, deposits, withdrawals, transfers, and
transaction history — with an automated test suite (unit, integration, and Selenium E2E)
managed with **Pytest**.

## Features

- User registration & login (hashed passwords, session-based auth via Flask-Login)
- Each user gets a bank account with an auto-generated account number
- Deposit, withdraw, and transfer money between accounts
- Full transaction history per account
- Server-side validation (positive amounts, sufficient funds, valid destination accounts)
- Bootstrap 5 UI

## Architecture (MVC)

```
app/
├── models.py              # Model layer — User, Account, Transaction (SQLAlchemy)
├── services/               # Business logic, independent of Flask/HTTP
│   ├── account_service.py  # deposit / withdraw / transfer / register_user
│   └── exceptions.py        # Domain-specific exceptions
├── routes/                 # Controller layer — Flask blueprints
│   ├── auth.py              # /register /login /logout
│   └── accounts.py          # /dashboard /deposit /withdraw /transfer /transactions
├── templates/               # View layer — Jinja2 + Bootstrap 5
└── static/css/style.css
```

Keeping the banking logic in `services/` (instead of directly in the routes) is what
makes the app easy to unit test — the tests below call `deposit()`, `withdraw()`, and
`transfer()` directly, with no Flask request/response involved at all.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Visit http://127.0.0.1:5000 register a user to get your first account.

## Running the tests

```bash
# Unit + integration tests (fast, no browser needed)
pytest -m "not e2e"

# Everything, including Selenium E2E (requires Chrome + chromedriver installed)
pytest

# With coverage
pytest -m "not e2e" --cov=app --cov-report=term-missing
```

**Current results on this codebase:**
- 91 automated tests total: 84 unit/integration tests + 7 Selenium end-to-end tests
- 96% statement coverage on the `app/` package (unit + integration tests only)

The E2E tests spin up the real Flask app on a background thread and drive it with a
headless Chrome browser via Selenium (register → login → deposit → withdraw →
transfer → logout). They're marked `@pytest.mark.e2e` and are skipped automatically
if Chrome/chromedriver isn't installed, so they never break the rest of the suite in
a browser-less CI environment.

## Tech stack

Python, Flask, Flask-SQLAlchemy, Flask-Login, SQLite, Selenium, Pytest, pytest-cov,
HTML/CSS, Bootstrap 5
