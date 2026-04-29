"""Talent.com FR — HTML scraper."""
import re
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class TalentFRScraper(BaseScraper):
    name = "talentfr"

    async def fetch(self) -> List[RawMission]:
        queries = ["freelance+developpeur", "freelance+react", "freelance+ia"]
        missions = []
        for query in queries:
            try:
                resp = await self._get(f"https://fr.talent.com/jobs?k={query}&l=France")
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(".card--job, .c-card, [class*='job-card']")[:15]:
                    title_el = card.select_one("h2, h3, [class*='title']")
                    company_el = card.select_one("[class*='company'], [class*='employer']")
                    link_el = card.select_one("a[href]")
                    salary_el = card.select_one("[class*='salary']")
                    if title_el:
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        if href and not href.startswith("http"):
                            href = f"https://fr.talent.com{href}"
                        missions.append(RawMission(
                            title=title_el.get_text(strip=True),
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
