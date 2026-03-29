# service_bot_backend/config.py
"""Centralized configuration — all env vars and file paths."""

import os

_dir = os.path.dirname(__file__)

# File paths (still file-based)
SERVICES_FILE = os.getenv("SERVICES_FILE", os.path.join(_dir, "services.json"))
AGENTS_FILE = os.getenv("AGENTS_FILE", os.path.join(_dir, "agents.md"))
SOUL_FILE = os.getenv("SOUL_FILE", os.path.join(_dir, "soul.md"))

# Database
DATABASE_FILE = os.getenv("DATABASE_FILE", os.path.join(_dir, "service_bot.db"))

# Auth
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")

# Thresholds
HANDOFF_THRESHOLD = int(os.getenv("HANDOFF_THRESHOLD", "2"))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "40"))

# Rate limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# WhatsApp Cloud API
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")

# Google Calendar
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "Africa/Johannesburg")

# Paystack
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")

# --- Runtime-mutable settings ---
# These can be changed via the /runtime/config API at runtime.
# The values below are defaults; the API loads overrides from the DB.

_MUTABLE_KEYS = {
    "MODEL_NAME", "HANDOFF_THRESHOLD", "MAX_HISTORY_MESSAGES",
    "MAX_MESSAGE_LENGTH", "RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW",
    "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_API_TOKEN", "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_API_VERSION", "GOOGLE_CREDENTIALS_FILE", "GOOGLE_CALENDAR_ID",
    "PAYSTACK_SECRET_KEY", "PAYSTACK_BASE_URL",
    "TIMEZONE",
}


def get_mutable_config() -> dict:
    """Return current values of all mutable config keys."""
    import config as cfg
    result = {}
    for key in _MUTABLE_KEYS:
        result[key] = getattr(cfg, key, "")
    return result


def apply_config_overrides(overrides: dict) -> dict:
    """Apply config overrides to module-level variables. Returns what was changed."""
    import config as cfg
    changed = {}
    for key, value in overrides.items():
        if key not in _MUTABLE_KEYS:
            continue
        # Type-cast integers
        if key in ("HANDOFF_THRESHOLD", "MAX_HISTORY_MESSAGES", "MAX_MESSAGE_LENGTH",
                    "RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW"):
            try:
                value = int(value)
            except (ValueError, TypeError):
                continue
        setattr(cfg, key, value)
        changed[key] = value
    return changed
