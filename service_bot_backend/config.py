"""Centralized configuration — all env vars and file paths."""

import os

_dir = os.path.dirname(__file__)

# File paths
SERVICES_FILE = os.getenv("SERVICES_FILE", os.path.join(_dir, "services.json"))
LEADS_FILE = os.getenv("LEADS_FILE", os.path.join(_dir, "leads.json"))
AGENTS_FILE = os.getenv("AGENTS_FILE", os.path.join(_dir, "agents.md"))
SOUL_FILE = os.getenv("SOUL_FILE", os.path.join(_dir, "soul.md"))
CONVERSATIONS_FILE = os.getenv("CONVERSATIONS_FILE", os.path.join(_dir, "conversations.json"))
CUSTOMERS_DIR = os.getenv("CUSTOMERS_DIR", os.path.join(_dir, "customers"))
FEATURES_FILE = os.getenv("FEATURES_FILE", os.path.join(_dir, "features.json"))

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
