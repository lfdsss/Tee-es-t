"""Base scraper with retry logic, rate limiting, and self-healing."""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import List
import httpx

from models import RawMission

logger = logging.getLogger("snb.scrapers")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

_failure_counts = {}
_active_strategy = {}


class BaseScraper(ABC):
    name: str = "base"
    max_retries: int = 3
    backoff_seconds: List[int] = [5, 15, 30]
    max_failures_before_heal: int = 3

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    @abstractmethod
    async def fetch(self) -> List[RawMission]:
        ...

    async def fetch_fallback(self) -> List[RawMission]:
        """Override in subclasses to provide alternative scraping strategies."""
        return []

    async def safe_fetch(self) -> List[RawMission]:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                missions = await self.fetch()
                if missions:
                    _failure_counts[self.name] = 0
                    logger.info(f"[{self.name}] OK — {len(missions)} missions")
                    return missions
                else:
                    _failure_counts[self.name] = _failure_counts.get(self.name, 0) + 1
                    fails = _failure_counts[self.name]
                    logger.warning(f"[{self.name}] 0 missions (échec #{fails})")
                    if fails >= self.max_failures_before_heal:
                        logger.info(f"[{self.name}] Auto-heal: tentative fallback")
                        fallback = await self._try_fallback()
                        if fallback:
                            _failure_counts[self.name] = 0
                            return fallback
                    return []
            except Exception as e:
                last_error = e
                wait = self.backoff_seconds[min(attempt, len(self.backoff_seconds) - 1)]
                logger.warning(f"[{self.name}] Tentative {attempt + 1}/{self.max_retries}: {e} — retry {wait}s")
                await asyncio.sleep(wait)

        _failure_counts[self.name] = _failure_counts.get(self.name, 0) + 1
        fails = _failure_counts[self.name]
        logger.error(f"[{self.name}] ÉCHEC #{fails}: {last_error}")
        if fails >= self.max_failures_before_heal:
            fallback = await self._try_fallback()
            if fallback:
                _failure_counts[self.name] = 0
                return fallback
        return []

    async def _try_fallback(self) -> List[RawMission]:
        try:
            missions = await self.fetch_fallback()
            if missions:
                logger.info(f"[{self.name}] Fallback OK — {len(missions)} missions")
                return missions
        except Exception as e:
            logger.error(f"[{self.name}] Fallback échoué: {e}")
        return []

    async def force_heal(self) -> List[RawMission]:
        """Called by /repair endpoint — tries all strategies."""
        logger.info(f"[{self.name}] Réparation forcée...")
        try:
            missions = await self.fetch()
            if missions:
                _failure_counts[self.name] = 0
                logger.info(f"[{self.name}] Réparation OK (méthode principale) — {len(missions)} missions")
                return missions
        except Exception as e:
            logger.warning(f"[{self.name}] Méthode principale échouée: {e}")

        try:
            missions = await self.fetch_fallback()
            if missions:
                _failure_counts[self.name] = 0
                logger.info(f"[{self.name}] Réparation OK (fallback) — {len(missions)} missions")
                return missions
        except Exception as e:
            logger.warning(f"[{self.name}] Fallback échoué: {e}")

        logger.error(f"[{self.name}] Réparation impossible — source probablement hors service")
        return []

    async def _get(self, url: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", self._headers())
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            return await client.get(url, headers=headers, **kwargs)

    async def _get_json(self, url: str, **kwargs) -> dict:
        resp = await self._get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()


def get_failure_counts() -> dict:
    return dict(_failure_counts)
