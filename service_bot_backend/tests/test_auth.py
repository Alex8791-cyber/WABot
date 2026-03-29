# service_bot_backend/tests/test_auth.py
import pytest
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_require_admin_passes_with_correct_token(monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    await require_admin(x_admin_token="secret123")

@pytest.mark.asyncio
async def test_require_admin_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(x_admin_token="wrong")
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_require_admin_generates_token_when_empty(monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "")
    monkeypatch.setattr("auth._generated_token", "")
    from auth import require_admin, get_admin_token
    token = get_admin_token()
    assert len(token) > 0
    # Should pass with the generated token
    await require_admin(x_admin_token=token)

@pytest.mark.asyncio
async def test_require_admin_rejects_empty_header_even_without_config(monkeypatch):
    monkeypatch.setattr("auth.cfg.ADMIN_TOKEN", "")
    monkeypatch.setattr("auth._generated_token", "")
    from auth import require_admin
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(x_admin_token=None)
    assert exc_info.value.status_code == 401
