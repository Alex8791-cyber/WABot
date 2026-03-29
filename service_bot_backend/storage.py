"""Persistence layer — SQLite for conversations/leads/features, files for config."""

import os
import re
import json
import logging
from typing import List, Dict, Any

from config import SERVICES_FILE, AGENTS_FILE, SOUL_FILE
from database import get_db

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


def sanitize_session_id(session_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)[:128]


# --- Services (still file-based) ---

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


# --- Conversations (SQLite) ---

def add_message(session_id: str, role: str, content: str) -> None:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.commit()
    finally:
        conn.close()


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT role, content FROM conversations WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    finally:
        conn.close()


def get_all_sessions() -> List[str]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT session_id FROM conversations ORDER BY session_id"
        ).fetchall()
        return [row["session_id"] for row in rows]
    finally:
        conn.close()


def get_all_conversation_history() -> Dict[str, List[Dict[str, str]]]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT session_id, role, content FROM conversations ORDER BY id"
        ).fetchall()
        history: Dict[str, List[Dict[str, str]]] = {}
        for row in rows:
            sid = row["session_id"]
            history.setdefault(sid, []).append(
                {"role": row["role"], "content": row["content"]}
            )
        return history
    finally:
        conn.close()


# --- Leads (SQLite) ---

def save_lead(lead_data: Dict[str, Any]) -> None:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO leads (service_id, responses) VALUES (?, ?)",
            (lead_data["service_id"], json.dumps(lead_data["responses"])),
        )
        conn.commit()
    finally:
        conn.close()


def get_leads() -> List[Dict[str, Any]]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT service_id, responses, created_at FROM leads ORDER BY id"
        ).fetchall()
        return [
            {
                "service_id": row["service_id"],
                "responses": json.loads(row["responses"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


# --- Feature config (SQLite) ---

def load_feature_config() -> Dict[str, Any]:
    config = {
        "enable_audio": os.getenv("ENABLE_AUDIO", "false").lower() == "true",
        "enable_images": os.getenv("ENABLE_IMAGES", "false").lower() == "true",
        "enable_tts": os.getenv("ENABLE_TTS", "false").lower() == "true",
        "whisper_model": os.getenv("WHISPER_MODEL") or None,
        "vision_api_key": os.getenv("VISION_API_KEY") or None,
    }
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM features").fetchall()
        for row in rows:
            key = row["key"]
            if key in config:
                val = row["value"]
                if key in ("enable_audio", "enable_images", "enable_tts"):
                    config[key] = val == "true"
                else:
                    config[key] = val if val else None
    except Exception as e:
        logger.error("Failed to load feature config: %s", e)
    finally:
        conn.close()
    return config


def save_feature_config(config: Dict[str, Any]) -> None:
    conn = get_db()
    try:
        for key, value in config.items():
            str_val = str(value).lower() if isinstance(value, bool) else (value or "")
            conn.execute(
                "INSERT OR REPLACE INTO features (key, value) VALUES (?, ?)",
                (key, str_val),
            )
        conn.commit()
    except Exception as e:
        logger.error("Failed to save feature config: %s", e)
    finally:
        conn.close()
