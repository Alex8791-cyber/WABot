# service_bot_backend/auth.py
"""Admin authentication dependency."""

import secrets
import logging
from typing import Optional
from fastapi import HTTPException, Header

import config as cfg

logger = logging.getLogger("service_bot")

_generated_token: str = ""


def get_admin_token() -> str:
    """Get the admin token — generates one if not configured."""
    global _generated_token
    if cfg.ADMIN_TOKEN:
        return cfg.ADMIN_TOKEN
    if not _generated_token:
        _generated_token = secrets.token_urlsafe(32)
        logger.warning(
            "ADMIN_TOKEN not set — generated temporary token: %s",
            _generated_token,
        )
        logger.warning("Set ADMIN_TOKEN env var for production use.")
    return _generated_token


async def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    token = get_admin_token()
    if x_admin_token != token:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")
