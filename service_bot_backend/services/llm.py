"""OpenAI LLM client with tool-calling support."""

import json
import logging
from typing import List, Dict

from fastapi import HTTPException

from config import OPENAI_API_KEY, MODEL_NAME, MAX_HISTORY_MESSAGES
from services.tools import get_tool_definitions, dispatch_tool

logger = logging.getLogger("service_bot")

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False
    OpenAI = None
    logger.warning("openai package not installed — LLM features disabled")

MAX_TOOL_ROUNDS = 5


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
    """Send a chat request with tool-calling support.

    The LLM may request tool calls (e.g. calendar operations). This function
    loops: execute tool calls, feed results back, until the LLM produces
    a final text response (max MAX_TOOL_ROUNDS iterations).
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(truncate_history(history))

    tools = get_tool_definitions()

    try:
        client = get_openai_client()

        for _ in range(MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
                max_tokens=1024,
            )
            msg = response.choices[0].message

            # No tool calls — return the text response
            if not msg.tool_calls:
                return msg.content or ""

            # Process tool calls
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                logger.info("Tool call: %s(%s)", fn_name, fn_args)

                result = dispatch_tool(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        # If we exhausted rounds, return whatever we have
        return msg.content or "I wasn't able to complete the request. Please try again."

    except HTTPException:
        raise
    except Exception as e:
        logger.error("LLM API error: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")
