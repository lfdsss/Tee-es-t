"""Codeur.com — HTML scraper for French freelance projects."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class CodeurScraper(BaseScraper):
    name = "codeur"

    async def fetch(self) -> List[RawMission]:
        missions = []
        for page in range(1, 4):
            try:
                resp = await self._get(f"https://www.codeur.com/projects?page={page}")
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(".project-item, .project-card, [class*='project']"):
                    title_el = card.select_one("h2, h3, .project-title, [class*='title']")
                    desc_el = card.select_one(".project-description, .description, p")
                    budget_el = card.select_one(".project-budget, .budget, [class*='budget']")
                    link_el = card.select_one("a[href*='/projects/']")
                    if title_el:
                        href = link_el["href"] if link_el and link_el.get("href") else ""
                        if href and not href.startswith("http"):
                            href = f"https://www.codeur.com{href}"
                        missions.append(RawMission(
                            title=title_el.get_text(strip=True),
                            company="",
                            description=desc_el.get_text(strip=True) if desc_el else "",
                            budget_raw=budget_el.get_text(strip=True) if budget_el else "",
                            source="codeur",
                            source_url=href,
                            tags=["freelance", "france"],
                            remote=True,
                        ))
            except Exception:
                pass
        return missions
