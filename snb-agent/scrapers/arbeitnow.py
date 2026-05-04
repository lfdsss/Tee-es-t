"""Arbeitnow — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class ArbeitnowScraper(BaseScraper):
    name = "arbeitnow"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://www.arbeitnow.com/api/job-board-api")
        missions = []
        for job in data.get("data", [])[:50]:
            missions.append(RawMission(
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                description=job.get("description", ""),
                budget_raw="",
                source="arbeitnow",
                source_url=job.get("url", ""),
                tags=job.get("tags", []),
                remote=job.get("remote", False),
            ))
        return missions
