import os

def test_config_defaults():
    """Config module exposes all expected constants with sane defaults."""
    from config import (
        SERVICES_FILE, LEADS_FILE, AGENTS_FILE, SOUL_FILE,
        CONVERSATIONS_FILE, CUSTOMERS_DIR, FEATURES_FILE,
        ADMIN_TOKEN, OPENAI_API_KEY, MODEL_NAME, VISION_MODEL,
        ALLOWED_ORIGINS, HANDOFF_THRESHOLD, MAX_MESSAGE_LENGTH,
        MAX_HISTORY_MESSAGES,
    )
    assert MODEL_NAME == "gpt-4o-mini"
    assert VISION_MODEL == "gpt-4o"
    assert HANDOFF_THRESHOLD == 2
    assert MAX_MESSAGE_LENGTH == 10000
    assert MAX_HISTORY_MESSAGES == 40
    assert "http://localhost:8080" in ALLOWED_ORIGINS

def test_config_override_via_env(monkeypatch):
    """Config picks up environment overrides."""
    monkeypatch.setenv("MODEL_NAME", "gpt-3.5-turbo")
    monkeypatch.setenv("HANDOFF_THRESHOLD", "5")
    # Force reimport
    import importlib
    import config
    importlib.reload(config)
    assert config.MODEL_NAME == "gpt-3.5-turbo"
    assert config.HANDOFF_THRESHOLD == 5
