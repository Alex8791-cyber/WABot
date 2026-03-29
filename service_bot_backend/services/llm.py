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
