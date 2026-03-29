# SQLite Storage Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace JSON file-based persistence (conversations, leads, features) with SQLite, eliminating full-file rewrites and enabling concurrent access.

**Architecture:** Introduce a `database.py` module that manages a single SQLite connection with WAL mode. Rewrite storage.py functions to use SQL instead of JSON files. Update routes/agent.py to remove the in-memory conversation dict and asyncio lock — all reads/writes go directly to SQLite. The public API of storage.py stays identical so routes/services/features don't change. Services catalog stays in `services.json` (static config). Agent config files (agents.md, soul.md) stay as files (edited at runtime).

**Tech Stack:** Python sqlite3 (stdlib), no new dependencies

---

## File Structure

```
service_bot_backend/
├── database.py          NEW — SQLite connection, schema init, get_db()
├── storage.py           MODIFY — rewrite conversation/lead/feature functions to use SQL
├── config.py            MODIFY — add DATABASE_FILE, remove CONVERSATIONS_FILE/LEADS_FILE/FEATURES_FILE/CUSTOMERS_DIR
├── routes/agent.py      MODIFY — remove in-memory dict, asyncio lock, bulk save; use storage functions directly
├── main.py              MODIFY — remove shutdown save, add DB init in lifespan
├── tests/test_database.py    NEW — schema creation, WAL mode
├── tests/test_storage.py     MODIFY — rewrite tests for SQLite-backed functions
├── tests/test_routes_agent.py MODIFY — update for new behavior (no in-memory state)
├── tests/conftest.py          MODIFY — add DB fixture
```

**What stays as files (NOT migrated):**
- `services.json` — static catalog, read-only
- `agents.md`, `soul.md` — markdown files editable at runtime
- `read_file()`, `write_file()`, `read_agents()`, `write_agents()`, `read_soul()`, `write_soul()`, `build_system_prompt()`, `load_services()` — unchanged
- `sanitize_session_id()` — still useful for any file-based operations

---

### Task 1: database.py — SQLite connection and schema

**Files:**
- Create: `service_bot_backend/database.py`
- Create: `service_bot_backend/tests/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_database.py
import sqlite3

def test_init_db_creates_tables(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    assert "conversations" in tables
    assert "leads" in tables
    assert "features" in tables
    conn.close()

def test_init_db_enables_wal(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()

def test_init_db_is_idempotent(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    init_db(db_path)  # second call should not fail
    conn = get_db()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "conversations" in tables
    conn.close()

def test_get_db_returns_connection(tmp_path):
    from database import init_db, get_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = get_db()
    assert conn is not None
    # Verify it's usable
    conn.execute("SELECT 1")
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_database.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 3: Write database.py**

```python
# service_bot_backend/database.py
"""SQLite database connection and schema management."""

import sqlite3
import logging

logger = logging.getLogger("service_bot")

_db_path: str = ""

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT NOT NULL,
    responses TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db(path: str) -> None:
    """Initialize the database: create tables and enable WAL mode."""
    global _db_path
    _db_path = path
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", path)


def get_db() -> sqlite3.Connection:
    """Get a new database connection."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_database.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/database.py service_bot_backend/tests/test_database.py
git commit -m "feat: add database.py with SQLite schema and connection management"
```

---

### Task 2: config.py — Add DATABASE_FILE, remove obsolete paths

**Files:**
- Modify: `service_bot_backend/config.py`
- Modify: `service_bot_backend/tests/test_config.py`

- [ ] **Step 1: Update test**

```python
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
    )
    assert MODEL_NAME == "gpt-4o-mini"
    assert VISION_MODEL == "gpt-4o"
    assert HANDOFF_THRESHOLD == 2
    assert MAX_MESSAGE_LENGTH == 10000
    assert MAX_HISTORY_MESSAGES == 40
    assert "http://localhost:8080" in ALLOWED_ORIGINS
    assert DATABASE_FILE.endswith("service_bot.db")

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'DATABASE_FILE'`

- [ ] **Step 3: Update config.py**

Replace the file paths section. Keep SERVICES_FILE, AGENTS_FILE, SOUL_FILE (still file-based). Remove LEADS_FILE, CONVERSATIONS_FILE, CUSTOMERS_DIR, FEATURES_FILE. Add DATABASE_FILE.

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
cd /d/WABot && git add service_bot_backend/config.py service_bot_backend/tests/test_config.py
git commit -m "feat: add DATABASE_FILE config, remove obsolete JSON file paths"
```

---

### Task 3: Rewrite storage.py — SQLite-backed persistence

**Files:**
- Modify: `service_bot_backend/storage.py`
- Modify: `service_bot_backend/tests/test_storage.py`

- [ ] **Step 1: Write the new tests**

Replace the entire `tests/test_storage.py` with tests that verify the SQLite-backed storage functions. The public API stays the same.

```python
# service_bot_backend/tests/test_storage.py
import json

def test_read_file_returns_content(tmp_path):
    from storage import read_file
    f = tmp_path / "test.md"
    f.write_text("hello world", encoding="utf-8")
    assert read_file(str(f)) == "hello world"

def test_read_file_returns_empty_for_missing():
    from storage import read_file
    assert read_file("/nonexistent/path/file.md") == ""

def test_write_file_creates_file(tmp_path):
    from storage import write_file
    path = str(tmp_path / "sub" / "test.txt")
    write_file(path, "content")
    assert open(path, encoding="utf-8").read() == "content"

def test_sanitize_session_id():
    from storage import sanitize_session_id
    assert sanitize_session_id("abc-123_def") == "abc-123_def"
    assert sanitize_session_id("a/b\\c:d") == "a_b_c_d"
    assert len(sanitize_session_id("x" * 200)) == 128

def test_load_services(tmp_path, monkeypatch):
    from storage import load_services
    path = tmp_path / "services.json"
    path.write_text('[{"id": "svc1", "name": "Test"}]', encoding="utf-8")
    monkeypatch.setattr("storage.SERVICES_FILE", str(path))
    result = load_services()
    assert result[0]["id"] == "svc1"

# --- SQLite-backed: conversations ---

def test_add_and_get_messages(test_db):
    from storage import add_message, get_session_history
    add_message("s1", "user", "hello")
    add_message("s1", "assistant", "hi there")
    history = get_session_history("s1")
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "hello"}
    assert history[1] == {"role": "assistant", "content": "hi there"}

def test_get_session_history_empty(test_db):
    from storage import get_session_history
    assert get_session_history("nonexistent") == []

def test_get_all_sessions(test_db):
    from storage import add_message, get_all_sessions
    add_message("s1", "user", "hi")
    add_message("s2", "user", "hello")
    sessions = get_all_sessions()
    assert set(sessions) == {"s1", "s2"}

def test_get_all_conversation_history(test_db):
    from storage import add_message, get_all_conversation_history
    add_message("s1", "user", "hi")
    add_message("s1", "assistant", "hello")
    add_message("s2", "user", "hey")
    history = get_all_conversation_history()
    assert "s1" in history
    assert "s2" in history
    assert len(history["s1"]) == 2
    assert len(history["s2"]) == 1

# --- SQLite-backed: leads ---

def test_save_and_get_leads(test_db):
    from storage import save_lead, get_leads
    save_lead({"service_id": "svc1", "responses": {"q1": "a1"}})
    save_lead({"service_id": "svc2", "responses": {"q2": "a2"}})
    leads = get_leads()
    assert len(leads) == 2
    assert leads[0]["service_id"] == "svc1"
    assert leads[0]["responses"] == {"q1": "a1"}

# --- SQLite-backed: features ---

def test_load_feature_config_defaults(test_db, monkeypatch):
    from storage import load_feature_config
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    config = load_feature_config()
    assert config["enable_audio"] is False
    assert config["enable_images"] is False

def test_save_and_load_feature_config(test_db, monkeypatch):
    from storage import save_feature_config, load_feature_config
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    save_feature_config({"enable_audio": True, "enable_images": False, "enable_tts": False})
    loaded = load_feature_config()
    assert loaded["enable_audio"] is True
    assert loaded["enable_images"] is False
```

- [ ] **Step 2: Update conftest.py with test_db fixture**

Add a `test_db` fixture that initializes a temp database before each test.

```python
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
    from routes import health, services, features, agent
    app = FastAPI()
    app.include_router(health.router)
    app.include_router(services.router)
    app.include_router(features.router)
    app.include_router(agent.router)
    return app


@pytest.fixture
def client(test_db):
    app = _create_test_app()
    return TestClient(app)


@pytest.fixture
def admin_client(test_db, monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "test-token")
    app = _create_test_app()
    c = TestClient(app)
    c.headers["x-admin-token"] = "test-token"
    return c
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd service_bot_backend && python -m pytest tests/test_storage.py -v`
Expected: FAIL — new functions `add_message`, `get_session_history`, etc. don't exist yet

- [ ] **Step 4: Rewrite storage.py**

Replace the entire file. Keep file-based functions (read_file, write_file, agents/soul, services, sanitize_session_id). Replace conversation, lead, and feature persistence with SQLite.

```python
# service_bot_backend/storage.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd service_bot_backend && python -m pytest tests/test_storage.py -v`
Expected: All passed

- [ ] **Step 6: Commit**

```bash
cd /d/WABot && git add service_bot_backend/storage.py service_bot_backend/tests/test_storage.py service_bot_backend/tests/conftest.py
git commit -m "feat: rewrite storage.py to use SQLite for conversations, leads, features"
```

---

### Task 4: Update routes/agent.py — Remove in-memory state, use SQLite

**Files:**
- Modify: `service_bot_backend/routes/agent.py`
- Modify: `service_bot_backend/tests/test_routes_agent.py`

- [ ] **Step 1: Update the test**

```python
# service_bot_backend/tests/test_routes_agent.py

def test_get_agent_config(client):
    resp = client.get("/agent/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert "soul" in data

def test_agent_message_without_llm(client):
    resp = client.post("/agent/message", json={
        "message": "Hello",
        "lang": "en"
    })
    # Without OPENAI_API_KEY, should return LLM unavailable fallback
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "session_id" in data

def test_agent_message_persists_to_db(client):
    resp = client.post("/agent/message", json={
        "message": "Hello",
        "session_id": "test-persist",
        "lang": "en"
    })
    assert resp.status_code == 200
    # Verify message was persisted
    from storage import get_session_history
    history = get_session_history("test-persist")
    assert len(history) >= 2  # user message + assistant reply
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"

def test_agent_message_empty_rejected(client):
    resp = client.post("/agent/message", json={"message": ""})
    assert resp.status_code == 422  # Pydantic validation
```

- [ ] **Step 2: Rewrite routes/agent.py**

Remove: `conversation_history` dict, `_state_lock`, `load_conversation_history`, `save_conversation_history`, `save_customer_history` imports.
Add: `add_message`, `get_session_history` imports.
Use storage functions directly — no in-memory state.

```python
# service_bot_backend/routes/agent.py
import uuid

from fastapi import APIRouter, Depends

from models import AgentMessage, AgentConfig
from auth import require_admin
from i18n import t
from storage import (
    read_agents, write_agents, read_soul, write_soul,
    build_system_prompt, add_message, get_session_history,
)
from services.sentiment import check_handoff
from services.llm import is_llm_available, chat
from services.multimedia import transcribe_audio, describe_image
import config as cfg

router = APIRouter()


@router.get("/agent/config")
def get_agent_config():
    return AgentConfig(
        agents=read_agents(),
        soul=read_soul(),
        api_key="***" if cfg.OPENAI_API_KEY else None,
    )


@router.post("/agent/config", dependencies=[Depends(require_admin)])
def update_agent_config(agent_config: AgentConfig):
    if agent_config.agents is not None:
        write_agents(agent_config.agents)
    if agent_config.soul is not None:
        write_soul(agent_config.soul)
    if agent_config.api_key is not None:
        cfg.OPENAI_API_KEY = agent_config.api_key
    return AgentConfig(
        agents=read_agents(),
        soul=read_soul(),
        api_key="***" if cfg.OPENAI_API_KEY else None,
    )


@router.post("/agent/message")
async def agent_message(msg: AgentMessage):
    lang = (msg.lang or "en").lower()
    session_id = msg.session_id or str(uuid.uuid4())

    # Process multimedia
    user_text = msg.message
    if msg.message_type == "audio" and msg.data_base64:
        user_text = transcribe_audio(msg.data_base64, lang)
    elif msg.message_type == "image" and msg.data_base64:
        user_text = describe_image(msg.data_base64, lang)

    # Persist user message
    add_message(session_id, "user", user_text)

    # Handoff check
    handoff_msg = check_handoff(session_id, user_text, lang)
    if handoff_msg:
        add_message(session_id, "assistant", handoff_msg)
        return {"reply": handoff_msg, "session_id": session_id, "handoff": True}

    # LLM fallback
    if not is_llm_available():
        fallback = t(lang, "llm_unavailable")
        add_message(session_id, "assistant", fallback)
        return {"reply": fallback, "session_id": session_id}

    # Build system prompt with language directive
    system_prompt = build_system_prompt()
    directive = t(lang, "directive")
    if directive:
        system_prompt = f"{directive}\n\n{system_prompt}" if system_prompt else directive

    # Get conversation history from DB for LLM context
    history = get_session_history(session_id)
    reply = chat(system_prompt, history)

    add_message(session_id, "assistant", reply)
    return {"reply": reply, "session_id": session_id}
```

- [ ] **Step 3: Run tests**

Run: `cd service_bot_backend && python -m pytest tests/test_routes_agent.py -v`
Expected: All passed

- [ ] **Step 4: Commit**

```bash
cd /d/WABot && git add service_bot_backend/routes/agent.py service_bot_backend/tests/test_routes_agent.py
git commit -m "feat: update routes/agent.py to use SQLite — remove in-memory state"
```

---

### Task 5: Update main.py — DB init in lifespan, remove shutdown save

**Files:**
- Modify: `service_bot_backend/main.py`

- [ ] **Step 1: Rewrite main.py**

```python
# service_bot_backend/main.py
"""AI Service Bot Backend — FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, DATABASE_FILE
from database import init_db
from routes import agent, services, features, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("service_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DATABASE_FILE)
    logger.info("Service Bot Backend starting")
    yield
    logger.info("Shutting down")


app = FastAPI(title="AI Service Bot API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(services.router)
app.include_router(features.router)
app.include_router(health.router)
```

- [ ] **Step 2: Run full test suite**

Run: `cd service_bot_backend && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Verify the app starts**

Run: `cd /d/WABot/service_bot_backend && timeout 5 python -m uvicorn main:app --host 0.0.0.0 --port 8000 2>&1 || true`
Expected: "Application startup complete" and "Database initialized"

- [ ] **Step 4: Commit**

```bash
cd /d/WABot && git add service_bot_backend/main.py
git commit -m "feat: init SQLite in lifespan, remove shutdown bulk save"
```

---

### Task 6: Update .gitignore and push

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Update .gitignore**

Replace the old JSON runtime data entries with the SQLite database file.

In `.gitignore`, replace:
```
# Backend runtime data
service_bot_backend/conversations.json
service_bot_backend/leads.json
service_bot_backend/features.json
service_bot_backend/customers/
```

With:
```
# Backend runtime data
service_bot_backend/*.db
service_bot_backend/*.db-wal
service_bot_backend/*.db-shm
```

- [ ] **Step 2: Run full test suite one final time**

Run: `cd /d/WABot/service_bot_backend && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Commit and push**

```bash
cd /d/WABot && git add .gitignore && git commit -m "chore: update .gitignore for SQLite, push SQLite migration"
git push origin main
```
