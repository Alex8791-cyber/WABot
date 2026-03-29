# service_bot_backend/tests/conftest.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_db(tmp_path):
    """Initialize a temporary SQLite database for testing."""
    from database import init_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)


def _create_test_app():
    """Create a minimal FastAPI app with new route modules for testing."""
    from routes import health, services, features, agent, webhook, calendar, payments
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(features.router)
    app.include_router(agent.router)
    app.include_router(webhook.router)
    app.include_router(calendar.router)
    app.include_router(payments.router)
    return app


@pytest.fixture
def client(test_db):
    app = _create_test_app()
    return TestClient(app)


@pytest.fixture
def admin_client(test_db, monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "test-token")
    app = _create_test_app()
    c = TestClient(app)
    c.headers["x-admin-token"] = "test-token"
    return c
