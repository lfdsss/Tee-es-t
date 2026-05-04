"""WorkingNomads — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class WorkingNomadsScraper(BaseScraper):
    name = "workingnomads"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://www.workingnomads.com/api/exposed_jobs/")
        missions = []
        for job in (data if isinstance(data, list) else [])[:50]:
            missions.append(RawMission(
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                description=job.get("description", ""),
                budget_raw="",
                source="workingnomads",
                source_url=job.get("url", ""),
                tags=[job.get("category_name", "")] if job.get("category_name") else [],
                remote=True,
            ))
        return missions
