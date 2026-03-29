# service_bot_backend/tests/conftest.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _create_test_app():
    """Create a minimal FastAPI app with new route modules for testing."""
    from routes import health, services, features, agent
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(features.router)
    app.include_router(agent.router)
    return app


@pytest.fixture
def client():
    app = _create_test_app()
    return TestClient(app)


@pytest.fixture
def admin_client(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "test-token")
    app = _create_test_app()
    c = TestClient(app)
    c.headers["x-admin-token"] = "test-token"
    return c
