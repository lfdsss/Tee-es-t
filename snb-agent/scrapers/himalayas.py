"""Himalayas — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class HimalayasScraper(BaseScraper):
    name = "himalayas"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://himalayas.app/jobs/api?limit=50")
        missions = []
        for job in data.get("jobs", []):
            missions.append(RawMission(
                title=job.get("title", ""),
                company=job.get("companyName", ""),
                description=job.get("description", ""),
                budget_raw=job.get("salary", "") or "",
                source="himalayas",
                source_url=f"https://himalayas.app/jobs/{job.get('slug', '')}",
                tags=job.get("categories", []),
                remote=True,
            ))
        return missions
