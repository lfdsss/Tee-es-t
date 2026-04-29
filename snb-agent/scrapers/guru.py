"""Guru.com — RSS scraper."""
import feedparser
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class GuruScraper(BaseScraper):
    name = "guru"

    async def fetch(self) -> List[RawMission]:
        resp = await self._get("https://www.guru.com/rss/jobs/")
        feed = feedparser.parse(resp.text)
        missions = []
        for entry in feed.entries[:30]:
            missions.append(RawMission(
                title=entry.get("title", ""),
                company="",
                description=entry.get("summary", ""),
                budget_raw="",
                source="guru",
                source_url=entry.get("link", ""),
                remote=True,
            ))
        return missions
