"""WeWorkRemotely — RSS feed scraper."""
import feedparser
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]

class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"

    async def fetch(self) -> List[RawMission]:
        missions = []
        for feed_url in FEEDS:
            resp = await self._get(feed_url)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:20]:
                missions.append(RawMission(
                    title=entry.get("title", ""),
                    company=entry.get("title", "").split(":")[0] if ":" in entry.get("title", "") else "",
                    description=entry.get("summary", ""),
                    budget_raw="",
                    source="weworkremotely",
                    source_url=entry.get("link", ""),
                    remote=True,
                ))
        return missions
