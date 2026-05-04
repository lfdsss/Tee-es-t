"""Notification channels.

Every channel implements `NotificationChannel.send(match, student, offer)`
and raises on failure. The `NotifierAgent` picks the right channel based on
runtime settings:

    - `email` (SMTP)   → EmailNotifier      (if SMTP_HOST set)
    - `webhook`        → WebhookNotifier    (if NOTIFICATION_WEBHOOK_URL set)
    - `null`           → NullNotifier       (default, marks as notified)

Adding a new channel is a single file: inherit `NotificationChannel`, plug
it into `build_notifier()`.
"""

from __future__ import annotations

from ..config import Settings
from .base import NotificationChannel, NullNotifier
from .email_smtp import EmailNotifier
from .webhook import WebhookNotifier


def build_notifier(settings: Settings) -> NotificationChannel:
    """Return the best notifier for the current settings.

    Priority: email → webhook → null. Email is preferred because it reaches
    the student directly; webhook is a bridge for Make/Zapier/n8n; null is
    a safe dev default that still marks matches as notified so the pipeline
    stays idempotent.
    """
    if settings.smtp_configured:
        return EmailNotifier(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            from_addr=settings.smtp_from,
            use_tls=settings.smtp_use_tls,
        )
    if settings.notification_webhook_url:
        return WebhookNotifier(settings.notification_webhook_url)
    return NullNotifier()


__all__ = [
    "EmailNotifier",
    "NotificationChannel",
    "NullNotifier",
    "WebhookNotifier",
    "build_notifier",
]
