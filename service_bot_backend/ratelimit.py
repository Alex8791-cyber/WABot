# service_bot_backend/ratelimit.py
"""Per-IP rate limiting for API endpoints."""

import time
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request

import config as cfg

logger = logging.getLogger("service_bot")

_requests: Dict[str, List[float]] = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _cleanup(timestamps: List[float], now: float, window: int) -> List[float]:
    cutoff = now - window
    return [ts for ts in timestamps if ts > cutoff]


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting."""
    limit = cfg.RATE_LIMIT_REQUESTS
    window = cfg.RATE_LIMIT_WINDOW

    if limit <= 0:
        return  # disabled

    ip = _get_client_ip(request)
    now = time.time()

    _requests[ip] = _cleanup(_requests[ip], now, window)

    if len(_requests[ip]) >= limit:
        logger.warning("Rate limit exceeded for %s", ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit} requests per {window}s.",
        )

    _requests[ip].append(now)
