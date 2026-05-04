"""In-memory pub/sub for the real-time match stream.

Lightweight broadcaster the MatcherAgent pushes to every time it creates a
match, and that the SSE endpoints fan out to connected browsers.

Two subscription axes:
  * `subscribe(student_id)` — student watching their inbox
  * `subscribe_offer(offer_id)` — employer watching incoming candidates

Design is deliberately modest: one `asyncio.Queue` per subscriber, keyed by
UUID. Fine for a single API process (the default Railway deployment). If
StudentFlow grows to multiple API workers, swap this module for Redis pub/sub
without touching any caller — the public surface is just `publish` / `subscribe`.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from uuid import UUID

log = logging.getLogger(__name__)


class MatchBroadcaster:
    """Fan-out queue keyed by student id OR offer id.

    `publish()` / `publish_offer()` are best-effort: they drop events rather
    than blocking if a subscriber's queue is saturated, so a slow browser can
    never stall the matcher.
    """

    def __init__(self, max_queue: int = 32) -> None:
        self._subs: dict[UUID, list[asyncio.Queue[dict]]] = defaultdict(list)
        self._offer_subs: dict[UUID, list[asyncio.Queue[dict]]] = defaultdict(list)
        self._max_queue = max_queue

    # ---- student axis ----

    def publish(self, student_id: UUID, event: dict) -> int:
        """Push `event` to every subscriber of `student_id`. Returns count."""
        return self._push(self._subs, student_id, event)

    @asynccontextmanager
    async def subscribe(self, student_id: UUID) -> AsyncIterator[asyncio.Queue[dict]]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=self._max_queue)
        self._subs[student_id].append(queue)
        try:
            yield queue
        finally:
            with suppress(ValueError):
                self._subs[student_id].remove(queue)
            if not self._subs[student_id]:
                self._subs.pop(student_id, None)

    # ---- offer / employer axis ----

    def publish_offer(self, offer_id: UUID, event: dict) -> int:
        """Push `event` to every employer subscriber watching this offer."""
        return self._push(self._offer_subs, offer_id, event)

    @asynccontextmanager
    async def subscribe_offer(self, offer_id: UUID) -> AsyncIterator[asyncio.Queue[dict]]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=self._max_queue)
        self._offer_subs[offer_id].append(queue)
        try:
            yield queue
        finally:
            with suppress(ValueError):
                self._offer_subs[offer_id].remove(queue)
            if not self._offer_subs[offer_id]:
                self._offer_subs.pop(offer_id, None)

    # ---- internal ----

    def _push(
        self,
        registry: dict[UUID, list[asyncio.Queue[dict]]],
        key: UUID,
        event: dict,
    ) -> int:
        queues = list(registry.get(key, ()))
        delivered = 0
        for q in queues:
            try:
                q.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                log.warning("Dropping SSE event for %s (queue full)", key)
        return delivered


# Module-level singleton. The API and the MatcherAgent both import this one.
broadcaster = MatchBroadcaster()
