"""Malt.fr — HTML scraper for French freelance missions."""
from typing import List
from models import RawMission
from scrapers.base import BaseScraper


class MaltScraper(BaseScraper):
    name = "malt"

    SEARCH_QUERIES = [
        "developpeur+react",
        "consultant+ia",
        "developpeur+web+freelance",
        "shopify+developer",
        "automatisation+ia",
    ]

    async def fetch(self) -> List[RawMission]:
        missions = []
        for query in self.SEARCH_QUERIES:
            try:
                resp = await self._get(
                    f"https://www.malt.fr/s?q={query}&as=t",
                    headers={
                        **self._headers(),
                        "Accept": "application/json, text/html, */*",
                    },
                )
                if resp.status_code != 200:
                    continue

                try:
                    data = resp.json()
                    results = data.get("results", data.get("freelancers", []))
                    if isinstance(results, list):
                        for item in results[:20]:
                            title = item.get("title", item.get("headline", ""))
                            if not title:
                                continue
                            missions.append(RawMission(
                                title=title,
                                company="Malt",
                                description=item.get("description", item.get("bio", "")),
                                budget_raw=item.get("averageDailyPrice", item.get("tjm", "")),
                                source="malt",
                                source_url=f"https://www.malt.fr{item.get('url', item.get('profileUrl', ''))}",
                                tags=item.get("skills", []) if isinstance(item.get("skills"), list) else [],
                                remote=True,
                            ))
                        continue
                except Exception:
                    pass

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select("[class*='project'], [class*='mission'], [class*='result'], article"):
                    title_el = card.select_one("h2, h3, [class*='title'], [class*='name']")
                    if not title_el:
                        continue
                    desc_el = card.select_one("[class*='description'], [class*='excerpt'], p")
                    budget_el = card.select_one("[class*='price'], [class*='budget'], [class*='rate']")
                    link_el = card.select_one("a[href]")
                    href = link_el["href"] if link_el and link_el.get("href") else ""
                    if href and not href.startswith("http"):
                        href = f"https://www.malt.fr{href}"
                    missions.append(RawMission(
                        title=title_el.get_text(strip=True),
                        company="Malt",
                        description=desc_el.get_text(strip=True) if desc_el else "",
                        budget_raw=budget_el.get_text(strip=True) if budget_el else "",
                        source="malt",
                        source_url=href,
                        tags=["freelance", "france"],
                        remote=True,
                    ))
            except Exception:
                pass
        return missions

    async def fetch_fallback(self) -> List[RawMission]:
        missions = []
        for query in self.SEARCH_QUERIES:
            try:
                resp = await self._get(f"https://www.malt.fr/s?q={query}&as=t")
                if resp.status_code != 200:
                    continue
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select("li[class], div[class*='card'], div[class*='item'], section[class]"):
                    title_el = card.select_one("h2, h3, h4, a > span, a > strong, [class*='title']")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if len(title) < 5:
                        continue
                    link_el = card.select_one("a[href]")
                    href = link_el["href"] if link_el and link_el.get("href") else ""
                    if href and not href.startswith("http"):
                        href = f"https://www.malt.fr{href}"
                    missions.append(RawMission(
                        title=title,
                        company="Malt",
                        description="",
                        budget_raw="",
                        source="malt",
                        source_url=href,
                        tags=["freelance", "france"],
                        remote=True,
                    ))
            except Exception:
                pass
        return missions
