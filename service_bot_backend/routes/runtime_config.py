# service_bot_backend/routes/runtime_config.py
"""Runtime configuration endpoint — read/write mutable settings."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends

from auth import require_admin
from database import get_db
from config import get_mutable_config, apply_config_overrides, _MUTABLE_KEYS

logger = logging.getLogger("service_bot")

router = APIRouter(prefix="/runtime", tags=["config"])

# Keys whose values should be masked in GET responses
_SECRET_KEYS = {
    "WHATSAPP_API_TOKEN", "PAYSTACK_SECRET_KEY", "SMTP_PASSWORD",
}


def _load_overrides_from_db() -> dict:
    """Load runtime config overrides from the database."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT key, value FROM runtime_config").fetchall()
        return {row["key"]: row["value"] for row in rows}
    except Exception:
        return {}
    finally:
        conn.close()


def _save_overrides_to_db(overrides: dict) -> None:
    """Save runtime config overrides to the database."""
    conn = get_db()
    try:
        for key, value in overrides.items():
            conn.execute(
                "INSERT OR REPLACE INTO runtime_config (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
        conn.commit()
    finally:
        conn.close()


def load_and_apply_db_overrides() -> None:
    """Load config overrides from DB and apply them. Called at startup."""
    overrides = _load_overrides_from_db()
    if overrides:
        applied = apply_config_overrides(overrides)
        if applied:
            logger.info("Applied %d runtime config overrides from DB", len(applied))


@router.get("/config", dependencies=[Depends(require_admin)])
def get_runtime_config():
    """Get all mutable runtime config values."""
    config = get_mutable_config()
    # Mask secrets
    masked = {}
    for key, value in config.items():
        if key in _SECRET_KEYS and value:
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


@router.post("/config", dependencies=[Depends(require_admin)])
def update_runtime_config(updates: Dict[str, str]):
    """Update runtime config values. Only keys in _MUTABLE_KEYS are accepted."""
    # Filter to valid keys
    valid = {k: v for k, v in updates.items() if k in _MUTABLE_KEYS}
    if not valid:
        return {"message": "No valid config keys provided", "changed": []}

    # Apply to running process
    changed = apply_config_overrides(valid)

    # Persist to DB
    _save_overrides_to_db(changed)

    logger.info("Runtime config updated: %s", list(changed.keys()))
    return {"message": "Config updated", "changed": list(changed.keys())}
