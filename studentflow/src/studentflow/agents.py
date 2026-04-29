"""Autonomous agent loops.

Three agents that the orchestrator launches concurrently. Each one is a
stateless loop that reads/writes through the Repository — no in-process state
so you can kill and restart them safely.
"""

from __future__ import annotations

import asyncio
import logging

from .config import Settings, get_settings
from .db import Repository
from .matching import rank_students_for_offer
from .models import Match, Offer
from .notifiers import NotificationChannel, build_notifier
from .realtime import broadcaster
from .scrapers import SCRAPERS, BaseScraper

log = logging.getLogger(__name__)


class ScraperAgent:
    """Calls every registered scraper in parallel and upserts offers."""

    def __init__(self, repo: Repository, scrapers: list[BaseScraper] | None = None) -> None:
        self.repo = repo
        self.scrapers = scrapers or [cls() for cls in SCRAPERS]  # type: ignore[call-arg]

    async def tick(self) -> int:
        results = await asyncio.gather(
            *(self._run_one(s) for s in self.scrapers), return_exceptions=True
        )
        all_offers: list[Offer] = []
        for scraper, result in zip(self.scrapers, results, strict=True):
            if isinstance(result, BaseException):
                log.exception("Scraper %s failed", scraper.source.value, exc_info=result)
                continue
            all_offers.extend(result)
        return self.repo.upsert_offers(all_offers)

    async def _run_one(self, scraper: BaseScraper) -> list[Offer]:
        log.info("Running scraper %s", scraper.source.value)
        offers = await scraper.fetch()
        log.info("Scraper %s returned %d offers", scraper.source.value, len(offers))
        return offers


class MatcherAgent:
    """Scores recent offers against active students and writes matches."""

    def __init__(self, repo: Repository, threshold: float) -> None:
        self.repo = repo
        self.threshold = threshold

    async def tick(self) -> int:
        offers = self.repo.list_recent_unmatched_offers()
        students = self.repo.list_active_students()
        if not offers or not students:
            return 0

        created = 0
        for offer in offers:
            ranked = rank_students_for_offer(offer, students, threshold=self.threshold)
            for student, result in ranked:
                match = Match(
                    offer_id=offer.id,
                    student_id=student.id,
                    score=result.score,
                    reasons=result.reasons,
                    distance_km=result.distance_km,
                )
                self.repo.insert_match(match)
                broadcaster.publish(
                    student.id,
                    {"type": "match", "match_id": str(match.id)},
                )
                broadcaster.publish_offer(
                    offer.id,
                    {"type": "candidate", "match_id": str(match.id), "student_id": str(student.id)},
                )
                created += 1
        log.info("MatcherAgent: %d matches created", created)
        return created


class NotifierAgent:
    """Dispatches unnotified matches through a pluggable `NotificationChannel`.

    The channel is decided at build time (`build_notifier(settings)`): email
    if SMTP is configured, else webhook, else a null channel that just logs.
    A failed send leaves `notified_at` null so the next tick retries; the
    loop is isolated per-match so one bad match can't poison the rest.
    """

    def __init__(self, repo: Repository, channel: NotificationChannel) -> None:
        self.repo = repo
        self.channel = channel

    async def tick(self) -> int:
        pending = self.repo.list_unnotified_matches()
        if not pending:
            return 0

        sent = 0
        for match in pending:
            student = self.repo.get_student(match.student_id)
            offer = self.repo.get_offer(match.offer_id)
            if student is None or offer is None:
                log.warning("NotifierAgent: skipping match %s (student or offer missing)", match.id)
                # Mark as notified anyway so we don't loop forever on orphans.
                self.repo.mark_match_notified(match.id)
                continue
            try:
                await self.channel.send(match=match, student=student, offer=offer)
                self.repo.mark_match_notified(match.id)
                sent += 1
            except Exception as exc:
                log.warning(
                    "NotifierAgent: channel=%s failed for match %s: %s",
                    self.channel.name,
                    match.id,
                    exc,
                )
        return sent


async def run_forever(repo: Repository, settings: Settings | None = None) -> None:
    """Launch the three agents concurrently and keep them running."""
    settings = settings or get_settings()

    scraper_agent = ScraperAgent(repo)
    matcher_agent = MatcherAgent(repo, threshold=settings.match_score_threshold)
    notifier_agent = NotifierAgent(repo, channel=build_notifier(settings))

    await asyncio.gather(
        _loop("scraper", scraper_agent.tick, settings.scraper_interval_seconds),
        _loop("matcher", matcher_agent.tick, settings.matcher_interval_seconds),
        _loop("notifier", notifier_agent.tick, settings.notifier_interval_seconds),
    )


async def _loop(name: str, tick_fn, interval: int) -> None:  # type: ignore[no-untyped-def]
    log.info("Starting %s loop (every %ds)", name, interval)
    while True:
        try:
            processed = await tick_fn()
            log.info("%s tick: %s items", name, processed)
        except Exception:
            log.exception("%s tick failed", name)
        await asyncio.sleep(interval)
