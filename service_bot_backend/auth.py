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
