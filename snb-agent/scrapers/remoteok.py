"""RemoteOK — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class RemoteOKScraper(BaseScraper):
    name = "remoteok"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://remoteok.com/api")
        missions = []
        for job in data[1:51]:  # Skip first (metadata)
            if not isinstance(job, dict):
                continue
            missions.append(RawMission(
                title=job.get("position", ""),
                company=job.get("company", ""),
                description=job.get("description", ""),
                budget_raw=job.get("salary", ""),
                source="remoteok",
                source_url=f"https://remoteok.com/remote-jobs/{job.get('slug', job.get('id', ''))}",
                tags=job.get("tags", []),
                remote=True,
            ))
        return missions
