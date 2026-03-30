"""Email service — send emails via SMTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

import config as cfg

logger = logging.getLogger("service_bot")


def is_configured() -> bool:
    return bool(cfg.SMTP_HOST and cfg.SMTP_USER and cfg.SMTP_PASSWORD)


def send_email(
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
) -> Dict[str, Any]:
    """Send an email via SMTP.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text body.
        html: Optional HTML body.
    """
    if not is_configured():
        return {"error": "Email not configured — set SMTP_HOST, SMTP_USER, SMTP_PASSWORD"}

    sender = cfg.SMTP_FROM or cfg.SMTP_USER

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as server:
            server.starttls()
            server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
            server.sendmail(sender, to, msg.as_string())

        logger.info("Email sent to %s: %s", to, subject)
        return {"status": "sent", "to": to, "subject": subject}

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return {"error": f"Failed to send email: {e}"}
