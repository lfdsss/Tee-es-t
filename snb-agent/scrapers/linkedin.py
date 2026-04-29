"""LinkedIn — Public guest search scraper with fallback selectors."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper


class LinkedInScraper(BaseScraper):
    name = "linkedin"

    QUERIES = [
        "freelance+developer+remote",
        "react+freelance+remote",
        "ai+consultant+freelance",
    ]

    async def _scrape_with_selectors(self, card_sel, title_sel, company_sel, link_sel) -> List[RawMission]:
        missions = []
        for query in self.QUERIES:
            try:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query}&location=France&start=0"
                resp = await self._get(url)
                if resp.status_code != 200:
                    continue
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(card_sel)[:15]:
                    title_el = card.select_one(title_sel)
                    if not title_el:
                        continue
                    company_el = card.select_one(company_sel)
                    link_el = card.select_one(link_sel)
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

    async def fetch(self) -> List[RawMission]:
        return await self._scrape_with_selectors(
            ".base-card",
            ".base-search-card__title",
            ".base-search-card__subtitle",
            "a.base-card__full-link",
        )

    async def fetch_fallback(self) -> List[RawMission]:
        return await self._scrape_with_selectors(
            "[class*='card'], li[class], article",
            "h3, h4, [class*='title']",
            "[class*='subtitle'], [class*='company'], span",
            "a[href*='linkedin.com/jobs'], a[href]",
        )
