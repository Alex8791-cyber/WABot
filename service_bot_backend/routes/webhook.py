# service_bot_backend/routes/webhook.py
"""WhatsApp Cloud API webhook — receive and reply to messages."""

import logging

from fastapi import APIRouter, Request, HTTPException, Query

import config as cfg
from i18n import t
from storage import add_message, get_session_history, build_system_prompt
from services.sentiment import check_handoff
from services.llm import is_llm_available, chat
from services.whatsapp import send_text_message, mark_as_read

logger = logging.getLogger("service_bot")

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification (GET challenge-response)."""
    if not cfg.WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    if hub_mode == "subscribe" and hub_verify_token == cfg.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)

    logger.warning("Webhook verification failed: mode=%s", hub_mode)
    raise HTTPException(status_code=403, detail="Verification failed")


def _extract_messages(body: dict) -> list:
    """Extract text messages from the webhook payload."""
    messages = []
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if "messages" not in value:
                continue
            contacts = {c["wa_id"]: c.get("profile", {}).get("name", "")
                        for c in value.get("contacts", [])}
            for msg in value["messages"]:
                if msg.get("type") == "text":
                    messages.append({
                        "from": msg["from"],
                        "name": contacts.get(msg["from"], ""),
                        "text": msg["text"]["body"],
                        "message_id": msg["id"],
                        "timestamp": msg.get("timestamp", ""),
                    })
    return messages


@router.post("")
async def receive_webhook(request: Request):
    """Process incoming WhatsApp messages."""
    body = await request.json()

    # WhatsApp sends status updates too — ignore them
    messages = _extract_messages(body)
    if not messages:
        return {"status": "ok"}

    for msg in messages:
        phone = msg["from"]
        text = msg["text"]
        message_id = msg["message_id"]

        # Use phone number as session ID for persistent conversations
        session_id = f"wa-{phone}"
        lang = "de"  # Default to German for WhatsApp users

        logger.info("WhatsApp message from %s: %s", phone, text[:50])

        # Mark as read
        mark_as_read(message_id)

        try:
            # Persist user message
            add_message(session_id, "user", text)

            # Handoff check
            handoff_msg = check_handoff(session_id, text, lang)
            if handoff_msg:
                add_message(session_id, "assistant", handoff_msg)
                send_text_message(phone, handoff_msg)
                continue

            # LLM fallback
            if not is_llm_available():
                fallback = t(lang, "llm_unavailable")
                add_message(session_id, "assistant", fallback)
                send_text_message(phone, fallback)
                continue

            # Build prompt and get LLM reply
            system_prompt = build_system_prompt()
            directive = t(lang, "directive")
            if directive:
                system_prompt = f"{directive}\n\n{system_prompt}" if system_prompt else directive

            history = get_session_history(session_id)
            reply = chat(system_prompt, history)

            add_message(session_id, "assistant", reply)
            send_text_message(phone, reply)

        except Exception as e:
            logger.error("Failed to process WhatsApp message from %s: %s", phone, e)
            error_msg = (
                "Es tut mir leid, es ist ein technischer Fehler aufgetreten. "
                "Bitte versuchen Sie es in wenigen Minuten erneut."
            )
            send_text_message(phone, error_msg)

    return {"status": "ok"}
