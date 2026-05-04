"""Landing.jobs — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class LandingJobsScraper(BaseScraper):
    name = "landingjobs"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://landing.jobs/api/v1/jobs?limit=30&remote=true")
        missions = []
        for job in (data if isinstance(data, list) else data.get("data", data.get("jobs", [])))[:30]:
            missions.append(RawMission(
                title=job.get("title", ""),
                company=job.get("company_name", job.get("company", "")),
                description=job.get("description", ""),
                budget_raw=job.get("salary", ""),
                source="landingjobs",
                source_url=job.get("url", job.get("link", "")),
                tags=job.get("tags", []),
                remote=True,
            ))
        return missions
