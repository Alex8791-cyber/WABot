# service_bot_backend/tests/test_routes_webhook.py
from unittest.mock import patch


def test_webhook_verify_success(client, monkeypatch):
    monkeypatch.setattr("config.WHATSAPP_VERIFY_TOKEN", "my-secret")
    # Need to reimport since config is read at call time
    monkeypatch.setattr("routes.webhook.cfg.WHATSAPP_VERIFY_TOKEN", "my-secret")
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "my-secret",
        "hub.challenge": "1234567890",
    })
    assert resp.status_code == 200
    assert resp.json() == 1234567890


def test_webhook_verify_wrong_token(client, monkeypatch):
    monkeypatch.setattr("routes.webhook.cfg.WHATSAPP_VERIFY_TOKEN", "my-secret")
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong-token",
        "hub.challenge": "123",
    })
    assert resp.status_code == 403


def test_webhook_verify_not_configured(client, monkeypatch):
    monkeypatch.setattr("routes.webhook.cfg.WHATSAPP_VERIFY_TOKEN", "")
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "",
        "hub.challenge": "123",
    })
    assert resp.status_code == 503


def test_webhook_receive_empty_payload(client):
    resp = client.post("/webhook", json={"entry": []})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_receive_status_update(client):
    """Status updates (delivered, read) should be ignored."""
    resp = client.post("/webhook", json={
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{"id": "msg1", "status": "delivered"}]
                }
            }]
        }]
    })
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("routes.webhook.send_text_message")
@patch("routes.webhook.mark_as_read")
def test_webhook_receive_text_message(mock_read, mock_send, client):
    """Incoming text message should be processed and replied to."""
    mock_send.return_value = True
    mock_read.return_value = True

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"wa_id": "4915112345678", "profile": {"name": "Test User"}}],
                    "messages": [{
                        "from": "4915112345678",
                        "id": "wamid.abc123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "Hallo, ich brauche Hilfe"}
                    }]
                }
            }]
        }]
    }

    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200

    # Verify message was sent back
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "4915112345678"  # phone number
    assert len(call_args[0][1]) > 0  # reply text not empty

    # Verify read receipt
    mock_read.assert_called_once_with("wamid.abc123")

    # Verify persisted to DB
    from storage import get_session_history
    history = get_session_history("wa-4915112345678")
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hallo, ich brauche Hilfe"


@patch("routes.webhook.send_text_message")
@patch("routes.webhook.mark_as_read")
@patch("routes.webhook.chat", side_effect=Exception("LLM exploded"))
@patch("routes.webhook.is_llm_available", return_value=True)
def test_webhook_sends_error_on_llm_failure(mock_available, mock_chat, mock_read, mock_send, client):
    """If LLM fails, user should get an error message, not silence."""
    mock_read.return_value = True

    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"wa_id": "4915112345678", "profile": {"name": "Test"}}],
                    "messages": [{
                        "from": "4915112345678",
                        "id": "wamid.err123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "Hello"}
                    }]
                }
            }]
        }]
    }

    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200

    # Verify error message was sent to user
    assert mock_send.call_count >= 1
    last_call_text = mock_send.call_args_list[-1][0][1]
    assert "fehler" in last_call_text.lower() or "erneut" in last_call_text.lower()


@patch("routes.webhook.send_text_message")
@patch("routes.webhook.mark_as_read")
def test_webhook_ignores_non_text_messages(mock_read, mock_send, client):
    """Non-text messages (images, audio) should be ignored for now."""
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "contacts": [{"wa_id": "4915112345678", "profile": {"name": "Test"}}],
                    "messages": [{
                        "from": "4915112345678",
                        "id": "wamid.abc456",
                        "timestamp": "1234567890",
                        "type": "image",
                        "image": {"id": "img123"}
                    }]
                }
            }]
        }]
    }

    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    mock_send.assert_not_called()
