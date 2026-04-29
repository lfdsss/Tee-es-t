"""LinkedIn — Public guest search scraper."""
import re
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class LinkedInScraper(BaseScraper):
    name = "linkedin"

    async def fetch(self) -> List[RawMission]:
        queries = ["freelance+developer+remote", "react+freelance+remote", "ai+consultant+freelance"]
        missions = []
        for query in queries:
            try:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query}&location=France&start=0"
                resp = await self._get(url)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(".base-card")[:15]:
                    title_el = card.select_one(".base-search-card__title")
                    company_el = card.select_one(".base-search-card__subtitle")
                    link_el = card.select_one("a.base-card__full-link")
                    if title_el:
                        missions.append(RawMission(
                            title=title_el.get_text(strip=True),
                            company=company_el.get_text(strip=True) if company_el else "",
                            description="",
                            budget_raw="",
                            source="linkedin",
                            source_url=link_el["href"].split("?")[0] if link_el and link_el.get("href") else "",
                            remote=True,
                        ))
            except Exception:
                pass
        return missions
