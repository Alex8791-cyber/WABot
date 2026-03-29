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
