"""Codeur.com — HTML scraper with fallback strategies."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper


class CodeurScraper(BaseScraper):
    name = "codeur"

    SELECTORS_PRIMARY = [
        ".project-item, .project-card, [class*='project']",
    ]
    SELECTORS_FALLBACK = [
        "article, .card, [class*='card'], [class*='listing']",
        "li[class], div[class*='row'], div[class*='item']",
    ]

    async def _scrape_with_selectors(self, selectors: list) -> List[RawMission]:
        missions = []
        for page in range(1, 4):
            try:
                resp = await self._get(f"https://www.codeur.com/projects?page={page}")
                if resp.status_code != 200:
                    continue
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for selector in selectors:
                    cards = soup.select(selector)
                    for card in cards:
                        title_el = card.select_one("h2, h3, h4, [class*='title'], a > strong, a > span")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        if len(title) < 10:
                            continue
                        desc_el = card.select_one("[class*='description'], [class*='excerpt'], p")
                        budget_el = card.select_one("[class*='budget'], [class*='price'], [class*='amount']")
                        link_el = card.select_one("a[href*='/projects/'], a[href*='/projet']")
                        if not link_el:
                            link_el = card.select_one("a[href]")
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        if href and not href.startswith("http"):
                            href = f"https://www.codeur.com{href}"
                        missions.append(RawMission(
                            title=title,
                            company="",
                            description=desc_el.get_text(strip=True) if desc_el else "",
                            budget_raw=budget_el.get_text(strip=True) if budget_el else "",
                            source="codeur",
                            source_url=href,
                            tags=["freelance", "france"],
                            remote=True,
                        ))
                    if missions:
                        break
            except Exception:
                pass
        return missions

    async def fetch(self) -> List[RawMission]:
        return await self._scrape_with_selectors(self.SELECTORS_PRIMARY)

    async def fetch_fallback(self) -> List[RawMission]:
        return await self._scrape_with_selectors(self.SELECTORS_FALLBACK)
