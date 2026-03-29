# service_bot_backend/tests/test_ratelimit.py
import time
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def clear_state():
    from ratelimit import _requests
    _requests.clear()


def _make_request(ip="127.0.0.1"):
    req = MagicMock()
    req.headers = {}
    req.client.host = ip
    return req


@pytest.mark.asyncio
async def test_allows_within_limit(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 5)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 60)
    from ratelimit import check_rate_limit
    req = _make_request()
    for _ in range(5):
        await check_rate_limit(req)  # should not raise


@pytest.mark.asyncio
async def test_blocks_over_limit(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 3)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 60)
    from ratelimit import check_rate_limit
    req = _make_request()
    for _ in range(3):
        await check_rate_limit(req)
    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(req)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_different_ips_independent(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 60)
    from ratelimit import check_rate_limit
    req_a = _make_request("10.0.0.1")
    req_b = _make_request("10.0.0.2")
    for _ in range(2):
        await check_rate_limit(req_a)
        await check_rate_limit(req_b)
    # a is at limit, b is at limit
    with pytest.raises(HTTPException):
        await check_rate_limit(req_a)
    with pytest.raises(HTTPException):
        await check_rate_limit(req_b)


@pytest.mark.asyncio
async def test_window_expires(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 1)
    from ratelimit import check_rate_limit
    req = _make_request()
    for _ in range(2):
        await check_rate_limit(req)
    time.sleep(1.1)  # wait for window to expire
    await check_rate_limit(req)  # should not raise


@pytest.mark.asyncio
async def test_disabled_when_zero(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 0)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 60)
    from ratelimit import check_rate_limit
    req = _make_request()
    for _ in range(100):
        await check_rate_limit(req)  # should never raise


@pytest.mark.asyncio
async def test_x_forwarded_for(monkeypatch):
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("ratelimit.cfg.RATE_LIMIT_WINDOW", 60)
    from ratelimit import check_rate_limit
    req = MagicMock()
    req.headers = {"x-forwarded-for": "203.0.113.50, 10.0.0.1"}
    req.client.host = "10.0.0.1"
    await check_rate_limit(req)
    with pytest.raises(HTTPException):
        await check_rate_limit(req)
    # Different forwarded IP is independent
    req2 = MagicMock()
    req2.headers = {"x-forwarded-for": "203.0.113.51"}
    req2.client.host = "10.0.0.1"
    await check_rate_limit(req2)  # should not raise
