"""Free-Work.com — Next.js SSR scraper."""
import json
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class FreeWorkScraper(BaseScraper):
    name = "freework"

    async def fetch(self) -> List[RawMission]:
        resp = await self._get("https://www.free-work.com/fr/tech-it/jobs?contracts=freelance")
        missions = []
        text = resp.text
        # Try to extract __NEXT_DATA__
        import re
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.DOTALL)
        if match:
            try:
                next_data = json.loads(match.group(1))
                props = next_data.get("props", {}).get("pageProps", {})
                jobs = props.get("jobs", props.get("results", props.get("data", [])))
                if isinstance(jobs, dict):
                    jobs = jobs.get("data", jobs.get("results", []))
                for job in (jobs if isinstance(jobs, list) else [])[:50]:
                    missions.append(RawMission(
                        title=job.get("title", job.get("name", "")),
                        company=job.get("company", {}).get("name", "") if isinstance(job.get("company"), dict) else str(job.get("company", "")),
                        description=job.get("description", ""),
                        budget_raw=job.get("salary", job.get("tjm", "")),
                        source="freework",
                        source_url=f"https://www.free-work.com/fr/tech-it/jobs/{job.get('slug', job.get('id', ''))}",
                        tags=job.get("skills", []) if isinstance(job.get("skills"), list) else [],
                        remote="remote" in str(job).lower(),
                    ))
                return missions
            except (json.JSONDecodeError, KeyError):
                pass
        # Fallback: HTML parsing
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        for card in soup.select("[class*='job'], [class*='mission'], article")[:30]:
            title_el = card.select_one("h2, h3, [class*='title']")
            if title_el:
                link_el = card.select_one("a[href]")
                href = link_el["href"] if link_el and link_el.get("href") else ""
                if href and not href.startswith("http"):
                    href = f"https://www.free-work.com{href}"
                missions.append(RawMission(
                    title=title_el.get_text(strip=True),
                    company="",
                    description="",
                    budget_raw="",
                    source="freework",
                    source_url=href,
                    tags=["freelance", "france"],
                    remote=True,
                ))
        return missions
