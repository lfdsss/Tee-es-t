"""Base scraper with retry logic and rate limiting."""

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


class BaseScraper(ABC):
    name: str = "base"
    max_retries: int = 3
    backoff_seconds: List[int] = [5, 15, 30]

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    @abstractmethod
    async def fetch(self) -> List[RawMission]:
        ...

    async def safe_fetch(self) -> List[RawMission]:
        for attempt in range(self.max_retries):
            try:
                missions = await self.fetch()
                return missions
            except Exception as e:
                wait = self.backoff_seconds[min(attempt, len(self.backoff_seconds) - 1)]
                logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {e} — retry in {wait}s")
                await asyncio.sleep(wait)
        logger.error(f"[{self.name}] All {self.max_retries} attempts failed")
        return []

    async def _get(self, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            return await client.get(url, headers=self._headers(), **kwargs)

    async def _get_json(self, url: str, **kwargs) -> dict:
        resp = await self._get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()
