"""Shared test fixtures.

Tests use a separate in-memory SQLite database (TestingConfig), so they never
touch your real MySQL data. Each test gets a brand-new empty database.
"""
import os
import sys
import uuid
import warnings

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
warnings.filterwarnings("ignore", message=".*Decimal objects natively.*")

from app import create_app  # noqa: E402
from app.config import TestingConfig  # noqa: E402
from app.extensions import db  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class ApiClient:
    """Wraps Flask's test client and sends the CSRF header automatically."""

    def __init__(self, flask_client):
        self.client = flask_client

    def _headers(self):
        cookie = self.client.get_cookie("csrf_access_token")
        return {"X-CSRF-TOKEN": cookie.value} if cookie else {}

    def get(self, url, **kw):
        return self.client.get(url, **kw)

    def post(self, url, json=None):
        return self.client.post(url, json=json if json is not None else {}, headers=self._headers())

    def put(self, url, json=None):
        return self.client.put(url, json=json or {}, headers=self._headers())

    def patch(self, url, json=None):
        return self.client.patch(url, json=json or {}, headers=self._headers())

    def delete(self, url):
        return self.client.delete(url, headers=self._headers())


def register(api, email=None, password="Secret123"):
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = api.post("/api/auth/register", {
        "name": "Test User", "email": email, "password": password, "confirm_password": password,
    })
    assert response.status_code == 201, response.get_json()
    return email


def create_household(api, budget=5000, planning_days=30):
    response = api.post("/api/household", {
        "household_name": "Test Home", "family_size": 4, "shopping_frequency": "Monthly",
        "monthly_budget": budget, "planning_period_days": planning_days,
    })
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]["household"]


def add_item(api, name="Rice", unit="kg", price=50, priority="Essential", **extra):
    payload = {"name": name, "category": "Rice and Grains", "unit": unit, "unit_price": price,
               "priority": priority, **extra}
    response = api.post("/api/groceries", payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["data"]["item"]


@pytest.fixture
def api(app):
    return ApiClient(app.test_client())


@pytest.fixture
def user_api(app):
    """A logged-in user who already has a household."""
    client = ApiClient(app.test_client())
    register(client)
    create_household(client)
    return client
