"""Jobicy — JSON API scraper."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class JobicyScraper(BaseScraper):
    name = "jobicy"

    async def fetch(self) -> List[RawMission]:
        data = await self._get_json("https://jobicy.com/api/v2/remote-jobs?count=50")
        missions = []
        for job in data.get("jobs", []):
            salary_min = None
            salary_max = None
            try:
                salary_min = float(job.get("annualSalaryMin", 0)) / 220 if job.get("annualSalaryMin") else None
                salary_max = float(job.get("annualSalaryMax", 0)) / 220 if job.get("annualSalaryMax") else None
            except (ValueError, TypeError):
                pass
            missions.append(RawMission(
                title=job.get("jobTitle", ""),
                company=job.get("companyName", ""),
                description=job.get("jobDescription", ""),
                budget_raw=job.get("annualSalaryMin", ""),
                source="jobicy",
                source_url=job.get("url", ""),
                tags=job.get("jobIndustry", []) if isinstance(job.get("jobIndustry"), list) else [],
                remote=True,
                budget_min=salary_min,
                budget_max=salary_max,
            ))
        return missions
