# service_bot_backend/tests/test_config.py
import os

def test_config_defaults():
    """Config module exposes all expected constants with sane defaults."""
    from config import (
        SERVICES_FILE, AGENTS_FILE, SOUL_FILE,
        DATABASE_FILE,
        ADMIN_TOKEN, OPENAI_API_KEY, MODEL_NAME, VISION_MODEL,
        ALLOWED_ORIGINS, HANDOFF_THRESHOLD, MAX_MESSAGE_LENGTH,
        MAX_HISTORY_MESSAGES,
        GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID,
    )
    assert MODEL_NAME == "gpt-4o-mini"
    assert VISION_MODEL == "gpt-4o"
    assert HANDOFF_THRESHOLD == 2
    assert MAX_MESSAGE_LENGTH == 10000
    assert MAX_HISTORY_MESSAGES == 40
    assert "http://localhost:8080" in ALLOWED_ORIGINS
    assert DATABASE_FILE.endswith("service_bot.db")
    assert GOOGLE_CREDENTIALS_FILE == ""
    assert GOOGLE_CALENDAR_ID == "primary"

def test_config_override_via_env(monkeypatch):
    """Config picks up environment overrides."""
    import importlib
    import config
    monkeypatch.setenv("MODEL_NAME", "gpt-3.5-turbo")
    monkeypatch.setenv("HANDOFF_THRESHOLD", "5")
    importlib.reload(config)
    assert config.MODEL_NAME == "gpt-3.5-turbo"
    assert config.HANDOFF_THRESHOLD == 5
    # Restore defaults so other tests aren't affected by the reload
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("HANDOFF_THRESHOLD", raising=False)
    importlib.reload(config)
