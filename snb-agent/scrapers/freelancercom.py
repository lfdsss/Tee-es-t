"""Freelancer.com — RSS scraper."""
import feedparser
from typing import List
from models import RawMission
from scrapers.base import BaseScraper

class FreelancerComScraper(BaseScraper):
    name = "freelancercom"

    async def fetch(self) -> List[RawMission]:
        feeds = [
            "https://www.freelancer.com/rss.xml",
        ]
        missions = []
        for feed_url in feeds:
            try:
                resp = await self._get(feed_url)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:30]:
                    budget_raw = ""
                    desc = entry.get("summary", "")
                    if "$" in desc:
                        import re
                        m = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', desc)
                        if m:
                            budget_raw = m.group()
                    missions.append(RawMission(
                        title=entry.get("title", ""),
                        company="",
                        description=desc,
                        budget_raw=budget_raw,
                        source="freelancercom",
                        source_url=entry.get("link", ""),
                        remote=True,
                    ))
            except Exception:
                pass
        return missions
