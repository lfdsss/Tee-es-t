"""Tests for agents using the in-memory repository."""

from __future__ import annotations

import pytest

from studentflow.agents import MatcherAgent, NotifierAgent, ScraperAgent
from studentflow.db import InMemoryRepository
from studentflow.models import Match, Offer, Source, Student
from studentflow.notifiers.base import NotificationChannel, NullNotifier
from studentflow.scrapers.base import BaseScraper

from .fixtures import make_offer, make_student


class _FakeScraper(BaseScraper):
    source = Source.INDEED

    def __init__(self, offers: list) -> None:  # type: ignore[no-untyped-def]
        self._offers = offers

    async def fetch(self):  # type: ignore[no-untyped-def]
        return self._offers


class _FailingScraper(BaseScraper):
    source = Source.HELLOWORK

    async def fetch(self):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_scraper_agent_upserts_and_isolates_errors() -> None:
    repo = InMemoryRepository()
    scrapers = [_FakeScraper([make_offer()]), _FailingScraper()]
    agent = ScraperAgent(repo, scrapers=scrapers)
    count = await agent.tick()
    assert count == 1
    assert len(repo.offers) == 1


@pytest.mark.asyncio
async def test_matcher_agent_creates_matches() -> None:
    repo = InMemoryRepository()
    repo.upsert_offers([make_offer()])
    student = make_student()
    repo.insert_student(student)

    agent = MatcherAgent(repo, threshold=0.6)
    created = await agent.tick()
    assert created == 1
    assert len(repo.matches) == 1


@pytest.mark.asyncio
async def test_notifier_agent_dispatches_via_null_channel() -> None:
    repo = InMemoryRepository()
    repo.upsert_offers([make_offer()])
    repo.insert_student(make_student())
    await MatcherAgent(repo, threshold=0.6).tick()

    notifier = NotifierAgent(repo, channel=NullNotifier())
    sent = await notifier.tick()
    assert sent == 1
    assert all(m.notified_at is not None for m in repo.matches.values())


class _RecordingChannel(NotificationChannel):
    name = "recording"

    def __init__(self) -> None:
        self.sent: list[tuple[Match, Student, Offer]] = []

    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        self.sent.append((match, student, offer))


class _BrokenChannel(NotificationChannel):
    name = "broken"

    async def send(self, *, match: Match, student: Student, offer: Offer) -> None:
        raise RuntimeError("smtp down")


@pytest.mark.asyncio
async def test_notifier_agent_passes_student_and_offer_to_channel() -> None:
    repo = InMemoryRepository()
    repo.upsert_offers([make_offer()])
    repo.insert_student(make_student())
    await MatcherAgent(repo, threshold=0.6).tick()

    channel = _RecordingChannel()
    sent = await NotifierAgent(repo, channel=channel).tick()

    assert sent == 1
    assert len(channel.sent) == 1
    match, student, offer = channel.sent[0]
    assert match.student_id == student.id
    assert match.offer_id == offer.id
    assert student.email == "emma@example.com"


@pytest.mark.asyncio
async def test_notifier_agent_keeps_match_unmarked_on_failure() -> None:
    repo = InMemoryRepository()
    repo.upsert_offers([make_offer()])
    repo.insert_student(make_student())
    await MatcherAgent(repo, threshold=0.6).tick()

    sent = await NotifierAgent(repo, channel=_BrokenChannel()).tick()
    assert sent == 0
    # Match stays unnotified so the next tick retries.
    assert all(m.notified_at is None for m in repo.matches.values())
