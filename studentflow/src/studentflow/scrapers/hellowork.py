"""HelloWork scraper via public RSS feed.

HelloWork exposes a public RSS 2.0 feed per search keyword. We fetch it, parse
each <item>, and map it to our `Offer` model. No authentication required,
no anti-bot handling, reasonably stable structure.

Example feed URL:
    https://www.hellowork.com/fr-fr/emploi/recherche.html?k=etudiant&rss=1

The RSS contract:
    <item>
      <title>Job title - Contract type - City</title>
      <link>https://.../offer/...</link>
      <description>HTML-ish summary</description>
      <pubDate>RFC-822 date</pubDate>
      <guid>unique stable id</guid>
    </item>

We stay defensive: missing fields fall back to empty strings, parse errors on a
single item skip that item rather than breaking the whole batch. Rate limits
are not aggressive but we keep a user agent for politeness.
"""

from __future__ import annotations

import logging
from xml.etree import ElementTree as ET

import httpx

from ..models import Offer, Source
from ..utils.skills import extract_skills
from ._text import extract_city_from_dashed_title, guess_contract, strip_html
from .base import BaseScraper

log = logging.getLogger(__name__)

FEED_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
USER_AGENT = "StudentFlow/0.1 (+https://github.com/them311/Tee-es-t)"


class HelloWorkScraper(BaseScraper):
    source = Source.HELLOWORK

    def __init__(self, *, keyword: str = "etudiant", max_results: int = 50) -> None:
        self._keyword = keyword
        self._max_results = max_results

    async def fetch(self) -> list[Offer]:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml"},
        ) as client:
            xml = await self._fetch_feed(client)
        return self._parse(xml)[: self._max_results]

    async def _fetch_feed(self, client: httpx.AsyncClient) -> bytes:
        resp = await client.get(FEED_URL, params={"k": self._keyword, "rss": 1})
        resp.raise_for_status()
        return resp.content

    def _parse(self, xml: bytes) -> list[Offer]:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            log.warning("HelloWork: RSS parse error: %s", exc)
            return []

        # RSS 2.0: <rss><channel><item>...</item></channel></rss>
        items = root.findall(".//item")
        offers: list[Offer] = []
        for item in items:
            try:
                offer = self._parse_item(item)
            except Exception as exc:
                log.warning("HelloWork: failed to parse item: %s", exc)
                continue
            if offer is not None:
                offers.append(offer)
        return offers

    def _parse_item(self, item: ET.Element) -> Offer | None:
        def text(tag: str) -> str:
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        title = text("title")
        if not title:
            return None

        link = text("link")
        description = strip_html(text("description"))
        guid = text("guid") or link or title

        contract = guess_contract(title + " " + description)
        city = extract_city_from_dashed_title(title)

        skills = extract_skills(f"{title}\n{description}")

        return Offer(
            source=Source.HELLOWORK,
            source_id=guid,
            title=title,
            description=description[:2000],
            company="",
            city=city,
            remote="télétravail" in (title + description).lower(),
            contract=contract,
            skills=skills,
            url=link,
        )
