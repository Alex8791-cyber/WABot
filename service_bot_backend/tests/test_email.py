from unittest.mock import patch, MagicMock


def test_is_configured_false(monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "")
    from services.email import is_configured
    assert is_configured() is False


def test_is_configured_true(monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr("services.email.cfg.SMTP_USER", "user@gmail.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PASSWORD", "pass123")
    from services.email import is_configured
    assert is_configured() is True


def test_send_email_not_configured(monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "")
    from services.email import send_email
    result = send_email("test@test.com", "Subject", "Body")
    assert "error" in result


@patch("services.email.smtplib.SMTP")
def test_send_email_success(mock_smtp, monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PORT", 587)
    monkeypatch.setattr("services.email.cfg.SMTP_USER", "bot@test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PASSWORD", "secret")
    monkeypatch.setattr("services.email.cfg.SMTP_FROM", "noreply@test.com")

    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    from services.email import send_email
    result = send_email("customer@firma.co.za", "Your Quote", "Here is your quote...")
    assert result["status"] == "sent"
    assert result["to"] == "customer@firma.co.za"
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("bot@test.com", "secret")
    mock_server.sendmail.assert_called_once()


@patch("services.email.smtplib.SMTP")
def test_send_email_with_html(mock_smtp, monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PORT", 587)
    monkeypatch.setattr("services.email.cfg.SMTP_USER", "bot@test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PASSWORD", "secret")
    monkeypatch.setattr("services.email.cfg.SMTP_FROM", "")

    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    from services.email import send_email
    result = send_email("x@y.com", "Test", "plain text", html="<h1>HTML</h1>")
    assert result["status"] == "sent"


@patch("services.email.smtplib.SMTP")
def test_send_email_smtp_error(mock_smtp, monkeypatch):
    monkeypatch.setattr("services.email.cfg.SMTP_HOST", "smtp.test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PORT", 587)
    monkeypatch.setattr("services.email.cfg.SMTP_USER", "bot@test.com")
    monkeypatch.setattr("services.email.cfg.SMTP_PASSWORD", "secret")
    monkeypatch.setattr("services.email.cfg.SMTP_FROM", "")

    mock_smtp.return_value.__enter__ = MagicMock(side_effect=Exception("Connection refused"))
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    from services.email import send_email
    result = send_email("x@y.com", "Test", "body")
    assert "error" in result
