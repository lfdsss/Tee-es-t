"""Talent.com FR — HTML scraper with fallback selectors."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper


class TalentFRScraper(BaseScraper):
    name = "talentfr"

    QUERIES = ["freelance+developpeur", "freelance+react", "freelance+ia"]

    async def _scrape_with_selectors(self, card_sel, title_sel, company_sel, salary_sel) -> List[RawMission]:
        missions = []
        for query in self.QUERIES:
            try:
                resp = await self._get(f"https://fr.talent.com/jobs?k={query}&l=France")
                if resp.status_code != 200:
                    continue
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(card_sel)[:15]:
                    title_el = card.select_one(title_sel)
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if len(title) < 5:
                        continue
                    company_el = card.select_one(company_sel)
                    link_el = card.select_one("a[href]")
                    salary_el = card.select_one(salary_sel)
                    href = link_el["href"] if link_el and link_el.get("href") else ""
                    if href and not href.startswith("http"):
                        href = f"https://fr.talent.com{href}"
                    missions.append(RawMission(
                        title=title,
                        company=company_el.get_text(strip=True) if company_el else "",
                        description="",
                        budget_raw=salary_el.get_text(strip=True) if salary_el else "",
                        source="talentfr",
                        source_url=href,
                        tags=["france"],
                        remote=True,
                    ))
            except Exception:
                pass
        return missions

    async def fetch(self) -> List[RawMission]:
        return await self._scrape_with_selectors(
            ".card--job, .c-card, [class*='job-card']",
            "h2, h3, [class*='title']",
            "[class*='company'], [class*='employer']",
            "[class*='salary']",
        )

    async def fetch_fallback(self) -> List[RawMission]:
        return await self._scrape_with_selectors(
            "article, li[class*='job'], div[class*='result'], [class*='listing']",
            "h2, h3, h4, a > span, a > strong, [class*='title']",
            "[class*='company'], [class*='name'], span + span",
            "[class*='salary'], [class*='pay'], [class*='wage']",
        )
