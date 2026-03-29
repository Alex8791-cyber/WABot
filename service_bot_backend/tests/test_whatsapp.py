# service_bot_backend/tests/test_whatsapp.py
from unittest.mock import patch, MagicMock


def test_send_text_message_not_configured(monkeypatch):
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_TOKEN", "")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_PHONE_NUMBER_ID", "")
    from services.whatsapp import send_text_message
    assert send_text_message("+4915112345678", "Hello") is False


def test_send_text_message_success(monkeypatch):
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_TOKEN", "test-token")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_VERSION", "v21.0")

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    from services.whatsapp import send_text_message
    with patch("services.whatsapp.httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(
            post=MagicMock(return_value=mock_resp)
        ))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        result = send_text_message("+4915112345678", "Hello")
        assert result is True


def test_send_text_message_api_error(monkeypatch):
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_TOKEN", "test-token")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_PHONE_NUMBER_ID", "12345")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_VERSION", "v21.0")

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"

    from services.whatsapp import send_text_message
    with patch("services.whatsapp.httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(return_value=MagicMock(
            post=MagicMock(return_value=mock_resp)
        ))
        mock_client.return_value.__exit__ = MagicMock(return_value=False)
        result = send_text_message("+4915112345678", "Hello")
        assert result is False


def test_mark_as_read_not_configured(monkeypatch):
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_API_TOKEN", "")
    monkeypatch.setattr("services.whatsapp.cfg.WHATSAPP_PHONE_NUMBER_ID", "")
    from services.whatsapp import mark_as_read
    assert mark_as_read("msg123") is False
