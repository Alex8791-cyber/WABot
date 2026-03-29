from unittest.mock import patch, MagicMock


def test_is_configured_false(monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "")
    from services.payments import is_configured
    assert is_configured() is False


def test_is_configured_true(monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "sk_test_123")
    from services.payments import is_configured
    assert is_configured() is True


def test_create_payment_link_not_configured(monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "")
    from services.payments import create_payment_link
    result = create_payment_link(
        amount=50000_00, email="test@test.co.za",
        service_name="Pentesting", session_id="s1",
    )
    assert "error" in result


@patch("services.payments.httpx.Client")
def test_create_payment_link_success(mock_client_cls, monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "sk_test_123")
    monkeypatch.setattr("services.payments.PAYSTACK_BASE_URL", "https://api.paystack.co")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": True,
        "data": {
            "reference": "ref_abc123",
            "authorization_url": "https://paystack.com/pay/abc123",
            "access_code": "ac_123",
        }
    }
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(
        post=MagicMock(return_value=mock_resp)
    ))
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    from services.payments import create_payment_link
    result = create_payment_link(
        amount=50000_00, email="test@test.co.za",
        service_name="Pentesting", session_id="s1",
    )
    assert result["payment_url"] == "https://paystack.com/pay/abc123"
    assert result["reference"] == "ref_abc123"


@patch("services.payments.httpx.Client")
def test_create_payment_link_api_error(mock_client_cls, monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "sk_test_123")
    monkeypatch.setattr("services.payments.PAYSTACK_BASE_URL", "https://api.paystack.co")

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad request"
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(
        post=MagicMock(return_value=mock_resp)
    ))
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    from services.payments import create_payment_link
    result = create_payment_link(
        amount=50000_00, email="test@test.co.za",
        service_name="Pentesting", session_id="s1",
    )
    assert "error" in result


@patch("services.payments.httpx.Client")
def test_verify_transaction_success(mock_client_cls, monkeypatch):
    monkeypatch.setattr("services.payments.PAYSTACK_SECRET_KEY", "sk_test_123")
    monkeypatch.setattr("services.payments.PAYSTACK_BASE_URL", "https://api.paystack.co")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": True,
        "data": {
            "status": "success",
            "reference": "ref_abc123",
            "amount": 5000000,
            "currency": "ZAR",
            "id": 12345,
            "paid_at": "2026-04-01T10:00:00Z",
        }
    }
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(
        get=MagicMock(return_value=mock_resp)
    ))
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

    from services.payments import verify_transaction
    result = verify_transaction("ref_abc123")
    assert result["status"] == "success"
    assert result["amount"] == 5000000
