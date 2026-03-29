import pytest
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_require_admin_passes_with_correct_token(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    # Should not raise
    await require_admin(x_admin_token="secret123")

@pytest.mark.asyncio
async def test_require_admin_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "secret123")
    from auth import require_admin
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(x_admin_token="wrong")
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_require_admin_passes_when_no_token_configured(monkeypatch):
    monkeypatch.setattr("auth.ADMIN_TOKEN", "")
    from auth import require_admin
    # Should not raise — unprotected mode
    await require_admin(x_admin_token=None)
