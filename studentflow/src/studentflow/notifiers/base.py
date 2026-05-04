"""Notifier base class and the null fallback."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ..models import Match, Offer, Student

log = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Each channel ships one match notification to one student.

    Implementations must raise on failure so the `NotifierAgent` can leave
    the match unmarked and retry on the next tick.
    """

    name: str

    @abstractmethod
    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        """Send the notification. Raise on failure."""


class NullNotifier(NotificationChannel):
    """No-op notifier used when nothing is configured.

    Still logs the match so you can see the pipeline is alive in dev.
    """

    name = "null"

    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        log.info(
            "NullNotifier: would notify %s about '%s' (score=%.2f)",
            student.email,
            offer.title,
            match.score,
        )
