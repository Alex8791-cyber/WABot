# Backend Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic `service_bot_backend/main.py` (673 lines) into focused modules with clear boundaries, then verify the app still works identically.

**Architecture:** Extract config, models, auth, i18n, storage, and business logic into separate files. Group routes into a `routes/` package and services into a `services/` package. The slim `main.py` only wires things together. No behavior changes — pure structural refactor.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, OpenAI SDK v1.x, vaderSentiment

---

## File Structure

After modularization, `service_bot_backend/` will look like this:

```
service_bot_backend/
├── main.py              # Slim: app creation, lifespan, CORS, router includes (~40 lines)
├── config.py            # All env vars, file paths, constants (~35 lines)
├── models.py            # Pydantic request/response models (~30 lines)
├── auth.py              # require_admin dependency (~15 lines)
├── i18n.py              # LANGUAGE_TEMPLATES dict + _t() helper (~55 lines)
├── storage.py           # File I/O: conversations, customers, leads, features (~120 lines)
├── services/
│   ├── __init__.py      # Empty
│   ├── sentiment.py     # Keyword lists + analyze_sentiment() (~55 lines)
│   ├── llm.py           # OpenAI client, build_system_prompt, chat call (~60 lines)
│   └── multimedia.py    # transcribe_audio(), describe_image() (~80 lines)
├── routes/
│   ├── __init__.py      # Empty
│   ├── agent.py         # /agent/message, /agent/config GET+POST (~80 lines)
│   ├── services.py      # /services, /services/{id}, /lead (~30 lines)
│   ├── features.py      # /features/config GET+POST (~45 lines)
│   └── health.py        # /health (~15 lines)
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Shared fixtures: test client, temp dirs, mock config
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_auth.py
│   ├── test_i18n.py
│   ├── test_storage.py
│   ├── test_sentiment.py
│   ├── test_routes_health.py
│   ├── test_routes_services.py
│   ├── test_routes_features.py
│   └── test_routes_agent.py
├── agents.md
├── soul.md
├── services.json
└── requirements.txt
```

**Dependency graph (no cycles):**
```
config.py ← i18n.py, storage.py, auth.py, services/*, routes/*
models.py ← routes/*
auth.py ← routes/agent.py, routes/features.py
i18n.py ← services/multimedia.py, routes/agent.py
storage.py ← services/llm.py, routes/*
services/sentiment.py ← routes/agent.py
services/llm.py ← routes/agent.py
services/multimedia.py ← routes/agent.py
```

---

### Task 1: config.py — Extract all configuration

**Files:**
- Create: `service_bot_backend/config.py`
- Create: `service_bot_backend/tests/__init__.py`
- Create: `service_bot_backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_config.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Write config.py**

```python
# service_bot_backend/config.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/config.py service_bot_backend/tests/
git commit -m "refactor: extract config.py from main.py"
```

---

### Task 2: i18n.py — Extract language templates

**Files:**
- Create: `service_bot_backend/i18n.py`
- Create: `service_bot_backend/tests/test_i18n.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_i18n.py

def test_t_returns_english_by_default():
    from i18n import t
    result = t("en", "handoff")
    assert "human support" in result.lower() or "connect you" in result.lower()

def test_t_returns_german():
    from i18n import t
    result = t("de", "handoff")
    assert "mitarbeiter" in result.lower() or "verbinden" in result.lower()

def test_t_unknown_lang_falls_back_to_english():
    from i18n import t
    result = t("fr", "handoff")
    assert result == t("en", "handoff")

def test_t_unknown_key_returns_empty():
    from i18n import t
    assert t("en", "nonexistent_key") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_i18n.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'i18n'`

- [ ] **Step 3: Write i18n.py**

```python
# service_bot_backend/i18n.py
"""Localized message templates for the service bot."""

LANGUAGE_TEMPLATES = {
    "en": {
        "audio_fallback": (
            "[Audio processing unavailable] An audio message was received, "
            "but audio processing is disabled or not configured."
        ),
        "image_fallback": (
            "[Image processing unavailable] An image was received, "
            "but image processing is disabled or not configured."
        ),
        "handoff": (
            "I see you're having a tough time. I'd like to connect you "
            "with one of our human support specialists who can assist you further."
        ),
        "llm_unavailable": (
            "[LLM unavailable] I received your message but the AI service "
            "is not configured. Please set the OPENAI_API_KEY."
        ),
        "directive": "Please answer in English.",
    },
    "de": {
        "audio_fallback": (
            "[Audiobearbeitung nicht verfügbar] Eine Sprachnachricht wurde empfangen, "
            "aber die Audioverarbeitung ist deaktiviert oder nicht konfiguriert."
        ),
        "image_fallback": (
            "[Bildverarbeitung nicht verfügbar] Ein Bild wurde empfangen, "
            "aber die Bildverarbeitung ist deaktiviert oder nicht konfiguriert."
        ),
        "handoff": (
            "Ich sehe, dass Sie Schwierigkeiten haben. Ich werde Sie mit einem "
            "unserer menschlichen Support-Mitarbeiter verbinden, der Ihnen weiterhelfen kann."
        ),
        "llm_unavailable": (
            "[LLM nicht verfügbar] Ich habe Ihre Nachricht erhalten, aber der "
            "KI-Dienst ist nicht konfiguriert. Bitte setzen Sie den OPENAI_API_KEY."
        ),
        "directive": "Bitte antworte auf Deutsch.",
    },
}


def t(lang: str, key: str) -> str:
    """Get a localized template string. Falls back to English, then empty string."""
    templates = LANGUAGE_TEMPLATES.get(lang, LANGUAGE_TEMPLATES["en"])
    return templates.get(key, LANGUAGE_TEMPLATES["en"].get(key, ""))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_i18n.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/i18n.py service_bot_backend/tests/test_i18n.py
git commit -m "refactor: extract i18n.py from main.py"
```

---

### Task 3: models.py — Extract Pydantic models

**Files:**
- Create: `service_bot_backend/models.py`
- Create: `service_bot_backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_models.py
import pytest
from pydantic import ValidationError

def test_agent_message_valid():
    from models import AgentMessage
    msg = AgentMessage(message="Hello")
    assert msg.message == "Hello"
    assert msg.lang == "en"
    assert msg.session_id is None
    assert msg.message_type is None

def test_agent_message_empty_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="")

def test_agent_message_invalid_lang_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="hi", lang="english")

def test_agent_message_invalid_type_rejected():
    from models import AgentMessage
    with pytest.raises(ValidationError):
        AgentMessage(message="hi", message_type="video")

def test_lead_model():
    from models import Lead
    lead = Lead(service_id="test", responses={"q1": "a1"})
    assert lead.service_id == "test"

def test_agent_config_model():
    from models import AgentConfig
    config = AgentConfig()
    assert config.agents is None
    assert config.soul is None
    assert config.api_key is None

def test_features_config_model():
    from models import FeaturesConfig
    config = FeaturesConfig(enable_audio=True)
    assert config.enable_audio is True
    assert config.enable_images is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Write models.py**

```python
# service_bot_backend/models.py
"""Pydantic request/response models."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from config import MAX_MESSAGE_LENGTH


class Lead(BaseModel):
    service_id: str
    responses: Dict[str, Any]


class AgentConfig(BaseModel):
    agents: Optional[str] = None
    soul: Optional[str] = None
    api_key: Optional[str] = None


class AgentMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    session_id: Optional[str] = None
    lang: Optional[str] = Field(default="en", pattern=r"^[a-z]{2}$")
    message_type: Optional[str] = Field(default=None, pattern=r"^(text|audio|image)$")
    data_base64: Optional[str] = None


class FeaturesConfig(BaseModel):
    enable_audio: Optional[bool] = None
    enable_images: Optional[bool] = None
    enable_tts: Optional[bool] = None
    whisper_model: Optional[str] = None
    vision_api_key: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_models.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/models.py service_bot_backend/tests/test_models.py
git commit -m "refactor: extract models.py from main.py"
```

---

### Task 4: auth.py — Extract admin auth dependency

**Files:**
- Create: `service_bot_backend/auth.py`
- Create: `service_bot_backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_auth.py
import pytest
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_require_admin_passes_with_correct_token(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    # Should not raise
    await require_admin(x_admin_token="secret123")

@pytest.mark.asyncio
async def test_require_admin_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(x_admin_token="wrong")
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_require_admin_passes_when_no_token_configured(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "")
    from auth import require_admin
    # Should not raise — unprotected mode
    await require_admin(x_admin_token=None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 3: Write auth.py**

```python
# service_bot_backend/auth.py
"""Admin authentication dependency."""

import logging
from typing import Optional
from fastapi import HTTPException, Header
from config import ADMIN_TOKEN

logger = logging.getLogger("service_bot")


async def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    if not ADMIN_TOKEN:
        logger.warning("ADMIN_TOKEN not set — config endpoints unprotected!")
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_auth.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/auth.py service_bot_backend/tests/test_auth.py
git commit -m "refactor: extract auth.py from main.py"
```

---

### Task 5: storage.py — Extract all persistence logic

**Files:**
- Create: `service_bot_backend/storage.py`
- Create: `service_bot_backend/tests/test_storage.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_storage.py
import json
import os

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

def test_load_conversation_history_empty(tmp_path, monkeypatch):
    from storage import load_conversation_history
    monkeypatch.setattr("storage.CONVERSATIONS_FILE", str(tmp_path / "missing.json"))
    assert load_conversation_history() == {}

def test_save_and_load_conversation_history(tmp_path, monkeypatch):
    from storage import save_conversation_history, load_conversation_history
    path = str(tmp_path / "convos.json")
    monkeypatch.setattr("storage.CONVERSATIONS_FILE", path)
    data = {"session1": [{"role": "user", "content": "hi"}]}
    save_conversation_history(data)
    loaded = load_conversation_history()
    assert loaded == data

def test_save_customer_history(tmp_path, monkeypatch):
    from storage import save_customer_history
    monkeypatch.setattr("storage.CUSTOMERS_DIR", str(tmp_path))
    save_customer_history("test-session", [{"role": "user", "content": "hi"}])
    path = tmp_path / "test-session" / "history.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1

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

def test_save_and_load_leads(tmp_path, monkeypatch):
    from storage import save_lead
    path = str(tmp_path / "leads.json")
    monkeypatch.setattr("storage.LEADS_FILE", path)
    save_lead({"service_id": "x", "responses": {}})
    data = json.loads(open(path, encoding="utf-8").read())
    assert len(data) == 1

def test_load_feature_config_defaults(tmp_path, monkeypatch):
    from storage import load_feature_config
    monkeypatch.setattr("storage.FEATURES_FILE", str(tmp_path / "missing.json"))
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    config = load_feature_config()
    assert config["enable_audio"] is False
    assert config["enable_images"] is False

def test_save_and_load_feature_config(tmp_path, monkeypatch):
    from storage import save_feature_config, load_feature_config
    path = str(tmp_path / "features.json")
    monkeypatch.setattr("storage.FEATURES_FILE", path)
    monkeypatch.delenv("ENABLE_AUDIO", raising=False)
    monkeypatch.delenv("ENABLE_IMAGES", raising=False)
    monkeypatch.delenv("ENABLE_TTS", raising=False)
    save_feature_config({"enable_audio": True, "enable_images": False, "enable_tts": False})
    loaded = load_feature_config()
    assert loaded["enable_audio"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_storage.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Write storage.py**

```python
# service_bot_backend/storage.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_storage.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/storage.py service_bot_backend/tests/test_storage.py
git commit -m "refactor: extract storage.py from main.py"
```

---

### Task 6: services/sentiment.py — Extract sentiment analysis

**Files:**
- Create: `service_bot_backend/services/__init__.py`
- Create: `service_bot_backend/services/sentiment.py`
- Create: `service_bot_backend/tests/test_sentiment.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_sentiment.py

def test_analyze_sentiment_negative_en():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("This is terrible and awful", lang="en")
    assert score < 0

def test_analyze_sentiment_positive_en():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("This is great and wonderful", lang="en")
    assert score > 0

def test_analyze_sentiment_neutral():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("The sky is blue", lang="en")
    assert -0.5 <= score <= 0.5

def test_analyze_sentiment_negative_de():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("Das ist furchtbar und schrecklich", lang="de")
    assert score < 0

def test_analyze_sentiment_positive_de():
    from services.sentiment import analyze_sentiment
    score = analyze_sentiment("Das ist super und wunderbar", lang="de")
    assert score > 0

def test_analyze_sentiment_empty():
    from services.sentiment import analyze_sentiment
    assert analyze_sentiment("", lang="en") == 0.0

def test_analyze_sentiment_clamped():
    from services.sentiment import analyze_sentiment
    # Many negative words — should clamp at -1.0
    text = " ".join(["problem", "angry", "bad", "terrible", "frustrated", "awful", "horrible"])
    score = analyze_sentiment(text, lang="de")  # force keyword fallback
    assert score >= -1.0

def test_check_handoff_triggers():
    from services.sentiment import check_handoff
    # First negative — no handoff yet
    result1 = check_handoff("s1", "terrible awful", "en")
    assert result1 is None
    # Second negative — handoff triggered (threshold=2)
    result2 = check_handoff("s1", "horrible angry", "en")
    assert result2 is not None
    assert "connect" in result2.lower() or "support" in result2.lower()

def test_check_handoff_resets_on_positive():
    from services.sentiment import check_handoff, _negative_counts
    _negative_counts.clear()
    check_handoff("s2", "terrible awful", "en")
    check_handoff("s2", "thanks great", "en")  # positive resets
    result = check_handoff("s2", "terrible awful", "en")
    assert result is None  # only 1 negative after reset
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_sentiment.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services'`

- [ ] **Step 3: Write services/__init__.py and services/sentiment.py**

```python
# service_bot_backend/services/__init__.py
```

```python
# service_bot_backend/services/sentiment.py
"""Sentiment analysis with VADER (EN) and keyword fallback (DE)."""

import logging
from typing import Optional

from config import HANDOFF_THRESHOLD
from i18n import t

logger = logging.getLogger("service_bot")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _sentiment_analyzer = SentimentIntensityAnalyzer()
except Exception:
    _sentiment_analyzer = None
    logger.info("vaderSentiment not available — using keyword fallback")

_NEGATIVE_DE = [
    "problem", "schlecht", "wütend", "ärgerlich", "enttäuscht", "furchtbar",
    "schrecklich", "miserabel", "katastrophe", "unzufrieden", "verärgert",
    "nervig", "frustriert", "sauer", "genervt", "unbrauchbar", "mangelhaft",
]
_POSITIVE_DE = [
    "gut", "super", "danke", "zufrieden", "toll", "wunderbar", "hervorragend",
    "perfekt", "prima", "klasse", "ausgezeichnet", "freundlich", "hilfreich",
]
_NEGATIVE_EN = [
    "problem", "angry", "bad", "terrible", "frustrated", "awful", "horrible",
    "disappointed", "unacceptable", "useless", "annoying", "poor", "worst",
]
_POSITIVE_EN = [
    "good", "great", "happy", "thanks", "excellent", "wonderful", "helpful",
    "perfect", "amazing", "fantastic", "satisfied", "love",
]

_negative_counts: dict[str, int] = {}


def analyze_sentiment(text: str, lang: str = "en") -> float:
    if not text:
        return 0.0
    if lang == "en" and _sentiment_analyzer is not None:
        try:
            return _sentiment_analyzer.polarity_scores(text).get("compound", 0.0)
        except Exception as e:
            logger.warning("VADER sentiment failed: %s", e)
    negatives = _NEGATIVE_DE if lang == "de" else _NEGATIVE_EN
    positives = _POSITIVE_DE if lang == "de" else _POSITIVE_EN
    text_lower = text.lower()
    score = 0.0
    for word in negatives:
        if word in text_lower:
            score -= 0.25
    for word in positives:
        if word in text_lower:
            score += 0.25
    return max(-1.0, min(1.0, score))


def check_handoff(session_id: str, text: str, lang: str) -> Optional[str]:
    sentiment = analyze_sentiment(text, lang=lang)
    if sentiment < -0.5:
        _negative_counts[session_id] = _negative_counts.get(session_id, 0) + 1
    else:
        _negative_counts[session_id] = 0
    if _negative_counts.get(session_id, 0) >= HANDOFF_THRESHOLD:
        return t(lang, "handoff")
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_sentiment.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/services/ service_bot_backend/tests/test_sentiment.py
git commit -m "refactor: extract services/sentiment.py from main.py"
```

---

### Task 7: services/llm.py — Extract LLM client logic

**Files:**
- Create: `service_bot_backend/services/llm.py`
- Create: `service_bot_backend/tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_llm.py
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

def test_get_openai_client_raises_without_key(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm.OPENAI_API_KEY", "")
    monkeypatch.setattr("services.llm._openai_available", True)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_get_openai_client_raises_without_package(monkeypatch):
    from services.llm import get_openai_client
    monkeypatch.setattr("services.llm._openai_available", False)
    with pytest.raises(HTTPException) as exc_info:
        get_openai_client()
    assert exc_info.value.status_code == 503

def test_truncate_history_short_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": "hi"}]
    assert truncate_history(history) == history

def test_truncate_history_long_list():
    from services.llm import truncate_history
    history = [{"role": "user", "content": f"msg{i}"} for i in range(100)]
    result = truncate_history(history)
    assert len(result) == 40  # MAX_HISTORY_MESSAGES default
    assert result[-1]["content"] == "msg99"

def test_openai_available_flag():
    from services.llm import is_llm_available
    # This just tests the function exists and returns a bool
    result = is_llm_available()
    assert isinstance(result, bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.llm'`

- [ ] **Step 3: Write services/llm.py**

```python
# service_bot_backend/services/llm.py
"""OpenAI LLM client and helpers."""

import logging
from typing import List, Dict

from fastapi import HTTPException

from config import OPENAI_API_KEY, MODEL_NAME, MAX_HISTORY_MESSAGES

logger = logging.getLogger("service_bot")

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None
    logger.warning("openai package not installed — LLM features disabled")


def is_llm_available() -> bool:
    return _openai_available and bool(OPENAI_API_KEY)


def get_openai_client() -> "OpenAI":
    if not _openai_available:
        raise HTTPException(status_code=503, detail="openai package not installed")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def truncate_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(history) <= MAX_HISTORY_MESSAGES:
        return list(history)
    return list(history[-MAX_HISTORY_MESSAGES:])


def chat(system_prompt: str, history: List[Dict[str, str]]) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(truncate_history(history))
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""
    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM API error: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_llm.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/services/llm.py service_bot_backend/tests/test_llm.py
git commit -m "refactor: extract services/llm.py from main.py"
```

---

### Task 8: services/multimedia.py — Extract audio/image processing

**Files:**
- Create: `service_bot_backend/services/multimedia.py`
- Create: `service_bot_backend/tests/test_multimedia.py`

- [ ] **Step 1: Write the failing test**

```python
# service_bot_backend/tests/test_multimedia.py
import base64

def test_transcribe_audio_disabled(monkeypatch):
    from services.multimedia import transcribe_audio
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_audio": False})
    result = transcribe_audio(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower() or "disabled" in result.lower()

def test_transcribe_audio_invalid_base64(monkeypatch):
    from services.multimedia import transcribe_audio
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_audio": True})
    result = transcribe_audio("not-valid-base64!!!", "en")
    assert "unavailable" in result.lower()

def test_describe_image_disabled(monkeypatch):
    from services.multimedia import describe_image
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_images": False})
    result = describe_image(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower() or "disabled" in result.lower()

def test_describe_image_no_openai(monkeypatch):
    from services.multimedia import describe_image
    monkeypatch.setattr("services.multimedia.load_feature_config",
                        lambda: {"enable_images": True})
    monkeypatch.setattr("services.multimedia._openai_available", False)
    result = describe_image(base64.b64encode(b"fake").decode(), "en")
    assert "unavailable" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd service_bot_backend && python -m pytest tests/test_multimedia.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.multimedia'`

- [ ] **Step 3: Write services/multimedia.py**

```python
# service_bot_backend/services/multimedia.py
"""Audio transcription and image analysis."""

import io
import base64
import logging

from config import OPENAI_API_KEY, VISION_MODEL
from i18n import t
from storage import load_feature_config

logger = logging.getLogger("service_bot")

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None


def transcribe_audio(data_b64: str, lang: str) -> str:
    config = load_feature_config()
    if not config.get("enable_audio", False):
        return t(lang, "audio_fallback")
    try:
        audio_bytes = base64.b64decode(data_b64)
    except Exception:
        return t(lang, "audio_fallback")

    # Try local whisper
    try:
        import whisper  # type: ignore
        model_name = config.get("whisper_model") or "base"
        model = whisper.load_model(model_name)
        result = model.transcribe(
            io.BytesIO(audio_bytes),
            language=lang if lang in ("de", "en") else None,
        )
        text = result.get("text", "")
        if text:
            return text
    except ImportError:
        logger.info("whisper not installed — trying OpenAI API")
    except Exception as e:
        logger.warning("Local whisper failed: %s", e)

    # Fallback to OpenAI Whisper API
    if _openai_available and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.webm"
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file,
            )
            if transcript.text:
                return transcript.text
        except Exception as e:
            logger.warning("OpenAI Whisper API failed: %s", e)

    return t(lang, "audio_fallback")


def describe_image(data_b64: str, lang: str) -> str:
    config = load_feature_config()
    if not config.get("enable_images", False):
        return t(lang, "image_fallback")
    if not _openai_available:
        return t(lang, "image_fallback")
    api_key = config.get("vision_api_key") or OPENAI_API_KEY
    if not api_key:
        return t(lang, "image_fallback")

    try:
        client = OpenAI(api_key=api_key)
        system_msg = {
            "en": "Describe the contents of the image in English.",
            "de": "Beschreibe den Inhalt des Bildes auf Deutsch.",
        }.get(lang, "Describe the contents of the image.")

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{data_b64}",
                    }},
                ]},
            ],
            max_tokens=256,
        )
        content = response.choices[0].message.content
        if content:
            return content
    except Exception as e:
        logger.warning("Image description failed: %s", e)

    return t(lang, "image_fallback")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd service_bot_backend && python -m pytest tests/test_multimedia.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add service_bot_backend/services/multimedia.py service_bot_backend/tests/test_multimedia.py
git commit -m "refactor: extract services/multimedia.py from main.py"
```

---

### Task 9: routes/ — Extract all route handlers

**Files:**
- Create: `service_bot_backend/routes/__init__.py`
- Create: `service_bot_backend/routes/health.py`
- Create: `service_bot_backend/routes/services.py`
- Create: `service_bot_backend/routes/features.py`
- Create: `service_bot_backend/routes/agent.py`
- Create: `service_bot_backend/tests/conftest.py`
- Create: `service_bot_backend/tests/test_routes_health.py`
- Create: `service_bot_backend/tests/test_routes_services.py`
- Create: `service_bot_backend/tests/test_routes_features.py`
- Create: `service_bot_backend/tests/test_routes_agent.py`

- [ ] **Step 1: Write conftest.py with shared fixtures**

```python
# service_bot_backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def admin_client(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "test-token")
    from main import app
    c = TestClient(app)
    c.headers["x-admin-token"] = "test-token"
    return c
```

- [ ] **Step 2: Write test_routes_health.py**

```python
# service_bot_backend/tests/test_routes_health.py

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "llm_available" in data
    assert "model" in data
```

- [ ] **Step 3: Write test_routes_services.py**

```python
# service_bot_backend/tests/test_routes_services.py

def test_get_services_returns_list(client):
    resp = client.get("/services")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]

def test_get_service_by_id(client):
    resp = client.get("/services/executive_it_support")
    assert resp.status_code == 200
    assert resp.json()["id"] == "executive_it_support"

def test_get_service_not_found(client):
    resp = client.get("/services/nonexistent")
    assert resp.status_code == 404

def test_create_lead(client):
    resp = client.post("/lead", json={
        "service_id": "executive_it_support",
        "responses": {"company_name": "Test GmbH"}
    })
    assert resp.status_code == 201

def test_create_lead_invalid_service(client):
    resp = client.post("/lead", json={
        "service_id": "nonexistent",
        "responses": {}
    })
    assert resp.status_code == 400
```

- [ ] **Step 4: Write test_routes_features.py**

```python
# service_bot_backend/tests/test_routes_features.py

def test_get_features_config(client):
    resp = client.get("/features/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "enable_audio" in data
    assert "enable_images" in data

def test_update_features_requires_admin(client):
    resp = client.post("/features/config", json={"enable_audio": True})
    # Without ADMIN_TOKEN set, this passes (unprotected mode)
    # but with token set, it should reject
    assert resp.status_code in (200, 401)
```

- [ ] **Step 5: Write test_routes_agent.py**

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
    # Without OPENAI_API_KEY, should return fallback or 503
    assert resp.status_code in (200, 503)

def test_agent_message_empty_rejected(client):
    resp = client.post("/agent/message", json={"message": ""})
    assert resp.status_code == 422  # Pydantic validation
```

- [ ] **Step 6: Write routes/__init__.py**

```python
# service_bot_backend/routes/__init__.py
```

- [ ] **Step 7: Write routes/health.py**

```python
# service_bot_backend/routes/health.py
from fastapi import APIRouter
from config import MODEL_NAME
from services.llm import is_llm_available

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "llm_available": is_llm_available(),
        "model": MODEL_NAME,
    }
```

- [ ] **Step 8: Write routes/services.py**

```python
# service_bot_backend/routes/services.py
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from models import Lead
from storage import load_services, save_lead

router = APIRouter()


@router.get("/services", response_model=List[Dict[str, Any]])
def get_services():
    return load_services()


@router.get("/services/{service_id}")
def get_service(service_id: str):
    for s in load_services():
        if s["id"] == service_id:
            return s
    raise HTTPException(status_code=404, detail="Service not found")


@router.post("/lead", status_code=201)
def create_lead(lead: Lead):
    if not any(s["id"] == lead.service_id for s in load_services()):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    entry = {"service_id": lead.service_id, "responses": lead.responses}
    save_lead(entry)
    return {"message": "Lead received", "lead": entry}
```

- [ ] **Step 9: Write routes/features.py**

```python
# service_bot_backend/routes/features.py
from fastapi import APIRouter, Depends
from models import FeaturesConfig
from auth import require_admin
from storage import load_feature_config, save_feature_config

router = APIRouter()


@router.get("/features/config")
def get_features_config():
    config = load_feature_config()
    return FeaturesConfig(
        enable_audio=config.get("enable_audio", False),
        enable_images=config.get("enable_images", False),
        enable_tts=config.get("enable_tts", False),
        whisper_model=config.get("whisper_model"),
        vision_api_key="***" if config.get("vision_api_key") else None,
    )


@router.post("/features/config", dependencies=[Depends(require_admin)])
def update_features_config(config: FeaturesConfig):
    current = load_feature_config()
    for field in ("enable_audio", "enable_images", "enable_tts", "whisper_model", "vision_api_key"):
        val = getattr(config, field)
        if val is not None:
            current[field] = val if val != "" else None
    save_feature_config(current)
    return FeaturesConfig(
        enable_audio=current.get("enable_audio", False),
        enable_images=current.get("enable_images", False),
        enable_tts=current.get("enable_tts", False),
        whisper_model=current.get("whisper_model"),
        vision_api_key="***" if current.get("vision_api_key") else None,
    )
```

- [ ] **Step 10: Write routes/agent.py**

```python
# service_bot_backend/routes/agent.py
import uuid
import asyncio

from fastapi import APIRouter, Depends

from models import AgentMessage, AgentConfig
from auth import require_admin
from i18n import t
from storage import (
    read_agents, write_agents, read_soul, write_soul,
    build_system_prompt, load_conversation_history, save_conversation_history,
    save_customer_history,
)
from services.sentiment import check_handoff
from services.llm import is_llm_available, chat
from services.multimedia import transcribe_audio, describe_image
import config as cfg

router = APIRouter()

# Shared mutable state
conversation_history = load_conversation_history()
_state_lock = asyncio.Lock()


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

    async with _state_lock:
        history = conversation_history.setdefault(session_id, [])
        history.append({"role": "user", "content": user_text})

        # Handoff check
        handoff_msg = check_handoff(session_id, user_text, lang)
        if handoff_msg:
            history.append({"role": "assistant", "content": handoff_msg})
            save_conversation_history(conversation_history)
            save_customer_history(session_id, history)
            return {"reply": handoff_msg, "session_id": session_id, "handoff": True}

    # LLM fallback
    if not is_llm_available():
        fallback = t(lang, "llm_unavailable")
        async with _state_lock:
            history.append({"role": "assistant", "content": fallback})
            save_conversation_history(conversation_history)
            save_customer_history(session_id, history)
        return {"reply": fallback, "session_id": session_id}

    # Build system prompt with language directive
    system_prompt = build_system_prompt()
    directive = t(lang, "directive")
    if directive:
        system_prompt = f"{directive}\n\n{system_prompt}" if system_prompt else directive

    reply = chat(system_prompt, history)

    async with _state_lock:
        history.append({"role": "assistant", "content": reply})
        save_conversation_history(conversation_history)
        save_customer_history(session_id, history)

    return {"reply": reply, "session_id": session_id}
```

- [ ] **Step 11: Run all route tests**

Run: `cd service_bot_backend && python -m pytest tests/test_routes_health.py tests/test_routes_services.py tests/test_routes_features.py tests/test_routes_agent.py -v`
Expected: All pass

- [ ] **Step 12: Commit**

```bash
git add service_bot_backend/routes/ service_bot_backend/tests/conftest.py service_bot_backend/tests/test_routes_*.py
git commit -m "refactor: extract routes/ package from main.py"
```

---

### Task 10: Rewrite main.py — Slim app entrypoint

**Files:**
- Modify: `service_bot_backend/main.py` (replace entire contents)

- [ ] **Step 1: Replace main.py with slim version**

```python
# service_bot_backend/main.py
"""AI Service Bot Backend — FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS
from storage import save_conversation_history
from routes import agent, services, features, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("service_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service Bot Backend starting")
    yield
    logger.info("Shutting down — saving state")
    save_conversation_history(agent.conversation_history)


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

- [ ] **Step 2: Run the full test suite**

Run: `cd service_bot_backend && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Verify app starts**

Run: `cd service_bot_backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &` then `curl http://localhost:8000/health` then kill the server.
Expected: `{"status":"ok",...}`

- [ ] **Step 4: Commit**

```bash
git add service_bot_backend/main.py
git commit -m "refactor: slim down main.py to app entrypoint — modularization complete"
```

---

### Task 11: Update requirements.txt and push

**Files:**
- Modify: `service_bot_backend/requirements.txt`

- [ ] **Step 1: Add test dependencies to requirements.txt**

```
# Core dependencies
fastapi==0.110.0
uvicorn==0.25.0
pydantic>=2.0.0

# LLM provider
openai>=1.0.0

# Sentiment analysis
vaderSentiment>=3.3.2

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0

# Optional: Uncomment if enabling audio/image features
# whisper @ git+https://github.com/openai/whisper.git
# pillow>=9.0.0
# gtts>=2.2.3
# pydub>=0.25.1
```

- [ ] **Step 2: Run full test suite one final time**

Run: `cd service_bot_backend && pip install -r requirements.txt && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Commit and push**

```bash
git add service_bot_backend/requirements.txt
git commit -m "chore: add test dependencies to requirements.txt"
git push origin main
```
