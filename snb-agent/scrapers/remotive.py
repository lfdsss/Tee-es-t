"""Remotive — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class RemotiveScraper(BaseScraper):
    name = "remotive"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://remotive.com/api/remote-jobs?limit=50")
        missions = []
        for job in data.get("jobs", []):
            missions.append(RawMission(
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                description=job.get("description", ""),
                budget_raw=job.get("salary", ""),
                source="remotive",
                source_url=job.get("url", ""),
                tags=job.get("tags", []),
                remote=True,
            ))
        return missions
