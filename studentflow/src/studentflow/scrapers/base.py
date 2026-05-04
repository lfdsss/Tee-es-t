"""Abstract base class for all scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Offer, Source


class BaseScraper(ABC):
    """Every concrete scraper implements `fetch()`.

    Rules:
      - No I/O in `__init__`. Clients and auth tokens are lazy.
      - `fetch()` must be idempotent: it should not mutate external state.
      - Raise exceptions freely — the `ScraperAgent` isolates each scraper.
      - Return typed `Offer` instances. `source_id` must be unique within the
        scraper's `Source`, so the DB upsert is deterministic.
    """

    source: Source

    @abstractmethod
    async def fetch(self) -> list[Offer]:
        """Fetch a batch of offers from the source. Can be called repeatedly."""
