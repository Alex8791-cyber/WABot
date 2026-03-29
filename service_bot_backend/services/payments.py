"""Paystack payment integration — create payment links and verify transactions."""

import logging
import uuid
from typing import Dict, Any, Optional

import httpx

from config import PAYSTACK_SECRET_KEY, PAYSTACK_BASE_URL

logger = logging.getLogger("service_bot")


def is_configured() -> bool:
    return bool(PAYSTACK_SECRET_KEY)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def create_payment_link(
    amount: int,
    email: str,
    service_name: str,
    session_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a Paystack payment link.

    Args:
        amount: Amount in kobo (ZAR cents). R50,000 = 5000000.
        email: Customer email for receipt.
        service_name: Name of the service being purchased.
        session_id: Optional session ID for tracking.
        description: Optional description.
    """
    if not is_configured():
        return {"error": "Paystack not configured — set PAYSTACK_SECRET_KEY"}

    reference = f"wabot-{uuid.uuid4().hex[:12]}"

    payload = {
        "amount": amount,
        "email": email,
        "currency": "ZAR",
        "reference": reference,
        "metadata": {
            "service_name": service_name,
            "session_id": session_id or "",
            "source": "wabot",
        },
    }
    if description:
        payload["metadata"]["description"] = description

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload, headers=_headers(),
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                logger.info("Payment link created: %s", reference)
                return {
                    "reference": data.get("reference", reference),
                    "payment_url": data.get("authorization_url", ""),
                    "access_code": data.get("access_code", ""),
                }
            logger.error("Paystack error %s: %s", resp.status_code, resp.text)
            return {"error": f"Paystack API error: {resp.status_code}"}
    except Exception as e:
        logger.error("Paystack request failed: %s", e)
        return {"error": str(e)}


def verify_transaction(reference: str) -> Dict[str, Any]:
    """Verify a Paystack transaction by reference."""
    if not is_configured():
        return {"error": "Paystack not configured"}

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=_headers(),
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "status": data.get("status", "unknown"),
                    "reference": data.get("reference", reference),
                    "amount": data.get("amount", 0),
                    "currency": data.get("currency", "ZAR"),
                    "paystack_id": data.get("id"),
                    "paid_at": data.get("paid_at"),
                }
            return {"error": f"Verification failed: {resp.status_code}"}
    except Exception as e:
        logger.error("Paystack verification failed: %s", e)
        return {"error": str(e)}
