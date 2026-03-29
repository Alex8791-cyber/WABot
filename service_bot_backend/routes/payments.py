"""Paystack payment endpoints — webhook for payment confirmation, status queries."""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Request, HTTPException, Query

import config as cfg
from database import get_db
from services.payments import verify_transaction

logger = logging.getLogger("service_bot")

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/webhook")
async def paystack_webhook(request: Request):
    """Receive Paystack webhook events (payment confirmation)."""
    # Verify webhook signature
    if cfg.PAYSTACK_SECRET_KEY:
        signature = request.headers.get("x-paystack-signature", "")
        body = await request.body()
        expected = hmac.new(
            cfg.PAYSTACK_SECRET_KEY.encode(),
            body,
            hashlib.sha512,
        ).hexdigest()
        if signature != expected:
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event", "")

    if event == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference", "")
        amount = data.get("amount", 0)
        paid_at = data.get("paid_at", "")
        paystack_id = str(data.get("id", ""))

        logger.info("Payment confirmed: %s (R%s)", reference, amount / 100)

        # Update payment record in DB
        conn = get_db()
        try:
            conn.execute(
                """UPDATE payments SET status = 'paid', paid_at = ?, paystack_id = ?
                   WHERE reference = ?""",
                (paid_at, paystack_id, reference),
            )
            conn.commit()
        finally:
            conn.close()

    return {"status": "ok"}


@router.get("/status/{reference}")
def get_payment_status(reference: str):
    """Check payment status by reference — checks DB first, then Paystack API."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT reference, status, amount, currency, email, service_id, paid_at FROM payments WHERE reference = ?",
            (reference,),
        ).fetchone()
    finally:
        conn.close()

    if row:
        return {
            "reference": row["reference"],
            "status": row["status"],
            "amount": row["amount"],
            "currency": row["currency"],
            "email": row["email"],
            "service_id": row["service_id"],
            "paid_at": row["paid_at"],
        }

    # Fallback: check Paystack API directly
    result = verify_transaction(reference)
    if "error" in result:
        raise HTTPException(status_code=404, detail="Payment not found")
    return result


@router.get("/list")
def list_payments(
    session_id: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50),
):
    """List payments, optionally filtered by session_id or status."""
    conn = get_db()
    try:
        query = "SELECT reference, session_id, service_id, amount, currency, email, status, payment_url, paid_at, created_at FROM payments"
        conditions = []
        params = []
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return {
            "payments": [
                {
                    "reference": r["reference"],
                    "session_id": r["session_id"],
                    "service_id": r["service_id"],
                    "amount": r["amount"],
                    "currency": r["currency"],
                    "email": r["email"],
                    "status": r["status"],
                    "payment_url": r["payment_url"],
                    "paid_at": r["paid_at"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        }
    finally:
        conn.close()
