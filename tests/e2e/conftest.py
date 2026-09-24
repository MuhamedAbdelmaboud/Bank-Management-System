import socket
import threading
import time

import pytest

from app import create_app, db as _db


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server_url():
    """Boot the Flask app in a background thread on a free port."""
    flask_app = create_app("config.TestConfig")
    with flask_app.app_context():
        _db.create_all()

    port = _free_port()
    server = threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=port, use_reloader=False),
        daemon=True,
    )
    server.start()
    time.sleep(1)  # give the server a moment to boot

    yield f"http://127.0.0.1:{port}"


@pytest.fixture
def browser():
    """A headless Chrome WebDriver, skipping the test if no browser is installed."""
    selenium = pytest.importorskip("selenium")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import WebDriverException

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome/Chromedriver not available in this environment: {exc}")

    yield driver
    driver.quit()
