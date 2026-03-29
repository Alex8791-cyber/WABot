"""
AI Service Bot Backend — FastAPI
=================================
A configurable AI chatbot backend with:
- LLM-powered chat via OpenAI-compatible API (v1.x+)
- Configurable personality via AGENTS.md / SOUL.md
- Sentiment-based human handoff
- Optional audio transcription and image analysis
- Per-session conversation persistence
- Admin authentication for config endpoints
"""

import io
import os
import re
import json
import uuid
import base64
import logging
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging — replaces all silent `except: pass` (Fix H-01)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("service_bot")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SERVICES_FILE = os.getenv("SERVICES_FILE", os.path.join(os.path.dirname(__file__), "services.json"))
LEADS_FILE = os.getenv("LEADS_FILE", os.path.join(os.path.dirname(__file__), "leads.json"))
AGENTS_FILE = os.getenv("AGENTS_FILE", os.path.join(os.path.dirname(__file__), "agents.md"))
SOUL_FILE = os.getenv("SOUL_FILE", os.path.join(os.path.dirname(__file__), "soul.md"))
CONVERSATIONS_FILE = os.getenv("CONVERSATIONS_FILE", os.path.join(os.path.dirname(__file__), "conversations.json"))
CUSTOMERS_DIR = os.getenv("CUSTOMERS_DIR", os.path.join(os.path.dirname(__file__), "customers"))
FEATURES_FILE = os.getenv("FEATURES_FILE", os.path.join(os.path.dirname(__file__), "features.json"))

# Auth (Fix K-02)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-4o")

# CORS (Fix K-03)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")

HANDOFF_THRESHOLD = int(os.getenv("HANDOFF_THRESHOLD", "2"))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "40"))

# ---------------------------------------------------------------------------
# OpenAI client — v1.x+ (Fix K-01)
# ---------------------------------------------------------------------------
try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    logger.warning("openai package not installed — LLM features disabled")

# ---------------------------------------------------------------------------
# Sentiment analysis
# ---------------------------------------------------------------------------
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _sentiment_analyzer = SentimentIntensityAnalyzer()
except Exception:
    _sentiment_analyzer = None
    logger.info("vaderSentiment not available — using keyword fallback")

# Thread-safe lock (Fix H-02)
_state_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Localized templates — single source of truth (Fix H-04)
# ---------------------------------------------------------------------------
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


def _t(lang: str, key: str) -> str:
    templates = LANGUAGE_TEMPLATES.get(lang, LANGUAGE_TEMPLATES["en"])
    return templates.get(key, LANGUAGE_TEMPLATES["en"].get(key, ""))


# ---------------------------------------------------------------------------
# Feature configuration
# ---------------------------------------------------------------------------


def _load_feature_config() -> Dict[str, Any]:
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


def _safe_makedirs(path: str) -> None:
    """Create parent directories only if path has a directory component (Fix H-07)."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def _save_feature_config(config: Dict[str, Any]) -> None:
    try:
        _safe_makedirs(FEATURES_FILE)
        with open(FEATURES_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error("Failed to save feature config: %s", e)


# ---------------------------------------------------------------------------
# Conversation persistence
# ---------------------------------------------------------------------------


def _load_conversation_history() -> Dict[str, List[Dict[str, str]]]:
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


def _save_conversation_history(history: Dict[str, List[Dict[str, str]]]) -> None:
    try:
        _safe_makedirs(CONVERSATIONS_FILE)
        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save conversation history: %s", e)


def _sanitize_session_id(session_id: str) -> str:
    """Create a filesystem-safe session ID (Fix M-05)."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)[:128]


def _save_customer_history(session_id: str, history: List[Dict[str, Any]]) -> None:
    try:
        safe_id = _sanitize_session_id(session_id)
        session_dir = os.path.join(CUSTOMERS_DIR, safe_id)
        os.makedirs(session_dir, exist_ok=True)
        path = os.path.join(session_dir, "history.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Failed to save customer history for %s: %s", session_id, e)


conversation_history: Dict[str, List[Dict[str, str]]] = _load_conversation_history()
negative_counts: Dict[str, int] = {}

# ---------------------------------------------------------------------------
# Sentiment analysis (Fix H-06 — extended German keywords)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Lead(BaseModel):
    service_id: str
    responses: Dict[str, Any]


class AgentConfig(BaseModel):
    agents: Optional[str] = None
    soul: Optional[str] = None
    api_key: Optional[str] = None


class AgentMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)  # Fix K-05, H-05
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


# ---------------------------------------------------------------------------
# Auth dependency (Fix K-02)
# ---------------------------------------------------------------------------


async def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    if not ADMIN_TOKEN:
        logger.warning("ADMIN_TOKEN not set — config endpoints unprotected!")
        return
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    _safe_makedirs(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_services() -> List[Dict[str, Any]]:
    try:
        with open(SERVICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Services file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid services JSON")


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


def build_system_prompt() -> str:
    parts = [p for p in [read_file(AGENTS_FILE).strip(), read_file(SOUL_FILE).strip()] if p]
    return "\n\n".join(parts)


def _get_openai_client() -> "OpenAI":
    """Create an OpenAI client (Fix K-01 — v1.x)."""
    if not _openai_available:
        raise HTTPException(status_code=503, detail="openai package not installed")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def _truncate_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep only recent messages to prevent token overflow (Fix K-07)."""
    if len(history) <= MAX_HISTORY_MESSAGES:
        return list(history)
    return list(history[-MAX_HISTORY_MESSAGES:])


# ---------------------------------------------------------------------------
# Multimedia processing (Fix K-04)
# ---------------------------------------------------------------------------


def transcribe_audio(data_b64: str, lang: str) -> str:
    config = _load_feature_config()
    if not config.get("enable_audio", False):
        return _t(lang, "audio_fallback")
    try:
        audio_bytes = base64.b64decode(data_b64)
    except Exception:
        return _t(lang, "audio_fallback")

    # Try local whisper
    try:
        import whisper  # type: ignore
        model_name = config.get("whisper_model") or "base"
        model = whisper.load_model(model_name)
        result = model.transcribe(io.BytesIO(audio_bytes), language=lang if lang in ("de", "en") else None)
        text = result.get("text", "")
        if text:
            return text
    except ImportError:
        logger.info("whisper not installed — trying OpenAI API")
    except Exception as e:
        logger.warning("Local whisper failed: %s", e)

    # Fallback to OpenAI Whisper API (v1.x)
    if _openai_available and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.webm"
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            if transcript.text:
                return transcript.text
        except Exception as e:
            logger.warning("OpenAI Whisper API failed: %s", e)

    return _t(lang, "audio_fallback")


def describe_image(data_b64: str, lang: str) -> str:
    config = _load_feature_config()
    if not config.get("enable_images", False):
        return _t(lang, "image_fallback")
    if not _openai_available:
        return _t(lang, "image_fallback")
    api_key = config.get("vision_api_key") or OPENAI_API_KEY
    if not api_key:
        return _t(lang, "image_fallback")

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
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data_b64}"}},
                ]},
            ],
            max_tokens=256,
        )
        content = response.choices[0].message.content
        if content:
            return content
    except Exception as e:
        logger.warning("Image description failed: %s", e)

    return _t(lang, "image_fallback")


# ---------------------------------------------------------------------------
# Handoff logic — single function (Fix H-04)
# ---------------------------------------------------------------------------


def _check_handoff(session_id: str, text: str, lang: str) -> Optional[str]:
    sentiment = analyze_sentiment(text, lang=lang)
    if sentiment < -0.5:
        negative_counts[session_id] = negative_counts.get(session_id, 0) + 1
    else:
        negative_counts[session_id] = 0
    if negative_counts.get(session_id, 0) >= HANDOFF_THRESHOLD:
        return _t(lang, "handoff")
    return None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Service Bot Backend starting")
    yield
    logger.info("Shutting down — saving state")
    _save_conversation_history(conversation_history)


app = FastAPI(title="AI Service Bot API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Service endpoints
# ---------------------------------------------------------------------------


@app.get("/services", response_model=List[Dict[str, Any]])
def get_services():
    return load_services()


@app.get("/services/{service_id}")
def get_service(service_id: str):
    for s in load_services():
        if s["id"] == service_id:
            return s
    raise HTTPException(status_code=404, detail="Service not found")


@app.post("/lead", status_code=201)
def create_lead(lead: Lead):
    if not any(s["id"] == lead.service_id for s in load_services()):
        raise HTTPException(status_code=400, detail="Invalid service ID")
    entry = {"service_id": lead.service_id, "responses": lead.responses}
    save_lead(entry)
    return {"message": "Lead received", "lead": entry}


# ---------------------------------------------------------------------------
# Feature config (GET public, POST protected)
# ---------------------------------------------------------------------------


@app.get("/features/config")
def get_features_config():
    config = _load_feature_config()
    return FeaturesConfig(
        enable_audio=config.get("enable_audio", False),
        enable_images=config.get("enable_images", False),
        enable_tts=config.get("enable_tts", False),
        whisper_model=config.get("whisper_model"),
        vision_api_key="***" if config.get("vision_api_key") else None,
    )


@app.post("/features/config", dependencies=[Depends(require_admin)])
def update_features_config(config: FeaturesConfig):
    current = _load_feature_config()
    for field in ("enable_audio", "enable_images", "enable_tts", "whisper_model", "vision_api_key"):
        val = getattr(config, field)
        if val is not None:
            current[field] = val if val != "" else None
    _save_feature_config(current)
    return FeaturesConfig(
        enable_audio=current.get("enable_audio", False),
        enable_images=current.get("enable_images", False),
        enable_tts=current.get("enable_tts", False),
        whisper_model=current.get("whisper_model"),
        vision_api_key="***" if current.get("vision_api_key") else None,
    )


# ---------------------------------------------------------------------------
# Agent config (GET public, POST protected)
# ---------------------------------------------------------------------------


@app.get("/agent/config")
def get_agent_config():
    return AgentConfig(
        agents=read_file(AGENTS_FILE),
        soul=read_file(SOUL_FILE),
        api_key="***" if OPENAI_API_KEY else None,
    )


@app.post("/agent/config", dependencies=[Depends(require_admin)])
def update_agent_config(config: AgentConfig):
    global OPENAI_API_KEY
    if config.agents is not None:
        write_file(AGENTS_FILE, config.agents)
    if config.soul is not None:
        write_file(SOUL_FILE, config.soul)
    if config.api_key is not None:
        OPENAI_API_KEY = config.api_key
    return AgentConfig(
        agents=read_file(AGENTS_FILE),
        soul=read_file(SOUL_FILE),
        api_key="***" if OPENAI_API_KEY else None,
    )


# ---------------------------------------------------------------------------
# Chat endpoint (all critical fixes applied)
# ---------------------------------------------------------------------------


@app.post("/agent/message")
async def agent_message(msg: AgentMessage):
    lang = (msg.lang or "en").lower()
    session_id = msg.session_id or str(uuid.uuid4())  # Fix K-06

    # Process multimedia (Fix K-04)
    user_text = msg.message
    if msg.message_type == "audio" and msg.data_base64:
        user_text = transcribe_audio(msg.data_base64, lang)
    elif msg.message_type == "image" and msg.data_base64:
        user_text = describe_image(msg.data_base64, lang)

    async with _state_lock:
        history = conversation_history.setdefault(session_id, [])
        history.append({"role": "user", "content": user_text})

        # Handoff check (Fix H-04 — single place)
        handoff_msg = _check_handoff(session_id, user_text, lang)
        if handoff_msg:
            history.append({"role": "assistant", "content": handoff_msg})
            _save_conversation_history(conversation_history)
            _save_customer_history(session_id, history)
            return {"reply": handoff_msg, "session_id": session_id, "handoff": True}

    # LLM fallback
    if not _openai_available or not OPENAI_API_KEY:
        fallback = _t(lang, "llm_unavailable")
        async with _state_lock:
            history.append({"role": "assistant", "content": fallback})
            _save_conversation_history(conversation_history)
            _save_customer_history(session_id, history)
        return {"reply": fallback, "session_id": session_id}

    # Build LLM messages
    system_prompt = build_system_prompt()
    directive = _t(lang, "directive")
    if directive:
        system_prompt = f"{directive}\n\n{system_prompt}" if system_prompt else directive

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(_truncate_history(history))  # Fix K-07

    # LLM call (Fix K-01 — v1.x client)
    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        reply = response.choices[0].message.content or ""
    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM API error: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")

    async with _state_lock:
        history.append({"role": "assistant", "content": reply})
        _save_conversation_history(conversation_history)
        _save_customer_history(session_id, history)

    return {"reply": reply, "session_id": session_id}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_available": _openai_available and bool(OPENAI_API_KEY),
        "model": MODEL_NAME,
    }
