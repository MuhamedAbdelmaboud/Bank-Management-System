"""
End-to-end browser tests using Selenium.

These tests drive a real (headless) Chrome browser against a live copy of the
Flask app to verify complete user journeys: registration, login, deposit,
withdrawal, transfer, and logout.

They are marked with @pytest.mark.e2e and are automatically skipped in any
environment where Chrome / chromedriver is not installed (see tests/e2e/conftest.py),
so the rest of the suite is unaffected when no browser is available (e.g. CI
containers without a display).
"""
import time
import uuid

import pytest
from selenium.webdriver.common.by import By

pytestmark = pytest.mark.e2e


def _unique_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def register_via_browser(browser, base_url, name, email, password, opening_balance="100"):
    browser.get(f"{base_url}/register")
    browser.find_element(By.NAME, "name").send_keys(name)
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys(password)
    balance_field = browser.find_element(By.NAME, "opening_balance")
    balance_field.clear()
    balance_field.send_keys(opening_balance)
    browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()


def login_via_browser(browser, base_url, email, password):
    browser.get(f"{base_url}/login")
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()


class TestRegistrationAndLoginFlow:
    def test_register_then_login_reaches_dashboard(self, browser, live_server_url):
        email = _unique_email()
        register_via_browser(browser, live_server_url, "Selenium User", email, "password1", "250")
        assert "login" in browser.current_url

        login_via_browser(browser, live_server_url, email, "password1")
        assert "dashboard" in browser.current_url or browser.current_url.rstrip("/") == live_server_url
        assert "250.00" in browser.page_source

    def test_invalid_login_shows_error(self, browser, live_server_url):
        browser.get(f"{live_server_url}/login")
        browser.find_element(By.NAME, "email").send_keys("nobody@example.com")
        browser.find_element(By.NAME, "password").send_keys("wrongpass")
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        assert "invalid email or password" in browser.page_source.lower()


class TestDepositFlow:
    def test_deposit_updates_balance(self, browser, live_server_url):
        email = _unique_email()
        register_via_browser(browser, live_server_url, "Deposit User", email, "password1", "100")
        login_via_browser(browser, live_server_url, email, "password1")

        browser.get(f"{live_server_url}/deposit")
        browser.find_element(By.NAME, "amount").send_keys("50")
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        assert "150.00" in browser.page_source


class TestWithdrawFlow:
    def test_withdraw_insufficient_funds_shows_error(self, browser, live_server_url):
        email = _unique_email()
        register_via_browser(browser, live_server_url, "Withdraw User", email, "password1", "20")
        login_via_browser(browser, live_server_url, email, "password1")

        browser.get(f"{live_server_url}/withdraw")
        browser.find_element(By.NAME, "amount").send_keys("999999")
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        assert "insufficient balance" in browser.page_source.lower()

    def test_valid_withdraw_updates_balance(self, browser, live_server_url):
        email = _unique_email()
        register_via_browser(browser, live_server_url, "Withdraw User 2", email, "password1", "100")
        login_via_browser(browser, live_server_url, email, "password1")

        browser.get(f"{live_server_url}/withdraw")
        browser.find_element(By.NAME, "amount").send_keys("40")
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        assert "60.00" in browser.page_source


class TestTransferFlow:
    def test_transfer_between_two_browser_created_accounts(self, browser, live_server_url):
        email_a = _unique_email()
        email_b = _unique_email()

        register_via_browser(browser, live_server_url, "Sender", email_a, "password1", "300")
        register_via_browser(browser, live_server_url, "Receiver", email_b, "password1", "0")

        # Grab receiver's account number by logging in as them briefly.
        login_via_browser(browser, live_server_url, email_b, "password1")
        page = browser.page_source
        start = page.find("Account #") + len("Account #")
        receiver_account_number = page[start:start + 10]
        browser.get(f"{live_server_url}/logout")

        login_via_browser(browser, live_server_url, email_a, "password1")
        browser.get(f"{live_server_url}/transfer")
        browser.find_element(By.NAME, "destination").send_keys(receiver_account_number)
        browser.find_element(By.NAME, "amount").send_keys("100")
        browser.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        assert "200.00" in browser.page_source


class TestLogoutFlow:
    def test_logout_returns_to_login_page(self, browser, live_server_url):
        email = _unique_email()
        register_via_browser(browser, live_server_url, "Logout User", email, "password1", "0")
        login_via_browser(browser, live_server_url, email, "password1")

        browser.get(f"{live_server_url}/logout")
        assert "login" in browser.current_url
        assert "logged out" in browser.page_source.lower()
