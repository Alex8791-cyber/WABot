"""File-based persistence for conversations, leads, features, and config files."""

import os
import re
import json
import logging
from typing import List, Dict, Any

from config import (
    SERVICES_FILE, LEADS_FILE, AGENTS_FILE, SOUL_FILE,
    CONVERSATIONS_FILE, CUSTOMERS_DIR, FEATURES_FILE,
)

logger = logging.getLogger("service_bot")


def _safe_makedirs(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


# --- Generic file I/O ---

def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    _safe_makedirs(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# --- Conversation persistence ---

def load_conversation_history() -> Dict[str, List[Dict[str, str]]]:
    if not os.path.exists(CONVERSATIONS_FILE):
        return {}
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {
                str(sid): list(msgs)
                for sid, msgs in data.items()
                if isinstance(msgs, list)
            }
    except Exception as e:
        logger.error("Failed to load conversation history: %s", e)
    return {}


def save_conversation_history(history: Dict[str, List[Dict[str, str]]]) -> None:
    try:
        _safe_makedirs(CONVERSATIONS_FILE)
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save conversation history: %s", e)


def sanitize_session_id(session_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)[:128]


def save_customer_history(session_id: str, history: List[Dict[str, Any]]) -> None:
    try:
        safe_id = sanitize_session_id(session_id)
        session_dir = os.path.join(CUSTOMERS_DIR, safe_id)
        os.makedirs(session_dir, exist_ok=True)
        path = os.path.join(session_dir, "history.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Failed to save customer history for %s: %s", session_id, e)


# --- Services ---

def load_services() -> List[Dict[str, Any]]:
    try:
        with open(SERVICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Services file not found")
    except json.JSONDecodeError:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Invalid services JSON")


# --- Leads ---

def save_lead(lead_data: Dict[str, Any]) -> None:
    leads = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Corrupted leads file — starting fresh")
    leads.append(lead_data)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


# --- Feature config ---

def load_feature_config() -> Dict[str, Any]:
    config = {
        "enable_audio": os.getenv("ENABLE_AUDIO", "false").lower() == "true",
        "enable_images": os.getenv("ENABLE_IMAGES", "false").lower() == "true",
        "enable_tts": os.getenv("ENABLE_TTS", "false").lower() == "true",
        "whisper_model": os.getenv("WHISPER_MODEL") or None,
        "vision_api_key": os.getenv("VISION_API_KEY") or None,
    }
    if os.path.exists(FEATURES_FILE):
        try:
            with open(FEATURES_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for key in config:
                    if key in saved:
                        config[key] = saved[key]
        except Exception as e:
            logger.error("Failed to load feature config: %s", e)
    return config


def save_feature_config(config: Dict[str, Any]) -> None:
    try:
        _safe_makedirs(FEATURES_FILE)
        with open(FEATURES_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error("Failed to save feature config: %s", e)


# --- Agent config files ---

def read_agents() -> str:
    return read_file(AGENTS_FILE)

def write_agents(content: str) -> None:
    write_file(AGENTS_FILE, content)

def read_soul() -> str:
    return read_file(SOUL_FILE)

def write_soul(content: str) -> None:
    write_file(SOUL_FILE, content)

def build_system_prompt() -> str:
    parts = [p for p in [read_agents().strip(), read_soul().strip()] if p]
    return "\n\n".join(parts)
