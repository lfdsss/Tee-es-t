"""Generic webhook notifier.

Posts a JSON payload to `NOTIFICATION_WEBHOOK_URL`. Works with Make, Zapier,
n8n, Discord, Slack, or any HTTP endpoint that can accept a JSON POST.
"""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from ..models import Match, Offer, Student
from .base import NotificationChannel

log = logging.getLogger(__name__)


class WebhookNotifier(NotificationChannel):
    name = "webhook"

    def __init__(self, url: str, *, timeout: float = 10.0) -> None:
        self.url = url
        self.timeout = timeout

    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        payload = {
            "match_id": str(match.id),
            "offer_id": str(match.offer_id),
            "student_id": str(match.student_id),
            "student_email": student.email,
            "student_full_name": student.full_name,
            "offer_title": offer.title,
            "offer_company": offer.company,
            "offer_city": offer.city,
            "offer_url": offer.url,
            "score": match.score,
            "reasons": match.reasons,
            "sent_at": datetime.utcnow().isoformat(),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.url, json=payload)
            resp.raise_for_status()
        log.info("WebhookNotifier: delivered match %s to %s", match.id, self.url)
