# service_bot_backend/services/whatsapp.py
"""WhatsApp Cloud API client — send messages via Meta Graph API."""

import logging
import httpx

import config as cfg

logger = logging.getLogger("service_bot")

_API_URL = "https://graph.facebook.com/{version}/{phone_id}/messages"


def _get_api_url() -> str:
    return _API_URL.format(
        version=cfg.WHATSAPP_API_VERSION,
        phone_id=cfg.WHATSAPP_PHONE_NUMBER_ID,
    )


def send_text_message(to: str, body: str) -> bool:
    """Send a text message to a WhatsApp number. Returns True on success."""
    if not cfg.WHATSAPP_API_TOKEN or not cfg.WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WhatsApp API not configured (missing token or phone number ID)")
        return False

    url = _get_api_url()
    headers = {
        "Authorization": f"Bearer {cfg.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                logger.info("WhatsApp message sent to %s", to)
                return True
            logger.error("WhatsApp API error %s: %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("WhatsApp send failed: %s", e)
        return False


def mark_as_read(message_id: str) -> bool:
    """Mark a received message as read."""
    if not cfg.WHATSAPP_API_TOKEN or not cfg.WHATSAPP_PHONE_NUMBER_ID:
        return False

    url = _get_api_url()
    headers = {
        "Authorization": f"Bearer {cfg.WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload, headers=headers)
            return resp.status_code == 200
    except Exception as e:
        logger.warning("Failed to mark message as read: %s", e)
        return False
