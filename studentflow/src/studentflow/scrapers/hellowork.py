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
import re
from xml.etree import ElementTree as ET

import httpx

from ..models import ContractType, Offer, Source
from ..utils.skills import extract_skills
from .base import BaseScraper

log = logging.getLogger(__name__)

FEED_URL = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
USER_AGENT = "StudentFlow/0.1 (+https://github.com/them311/Tee-es-t)"

# Rough mapping of French contract keywords to our enum. Case-insensitive.
CONTRACT_PATTERNS: list[tuple[re.Pattern[str], ContractType]] = [
    (re.compile(r"\b(stage|stagiaire)\b", re.I), ContractType.INTERNSHIP),
    (re.compile(r"\b(alternance|apprentissage|apprenti)\b", re.I), ContractType.APPRENTICESHIP),
    (re.compile(r"\bcdi\b", re.I), ContractType.CDI),
    (re.compile(r"\bcdd\b", re.I), ContractType.CDD),
    (
        re.compile(r"\b(temps partiel|part.?time|week.?end|job étudiant)\b", re.I),
        ContractType.PART_TIME,
    ),
    (re.compile(r"\b(freelance|indépendant|independant)\b", re.I), ContractType.FREELANCE),
]

# Strip HTML tags without pulling in BeautifulSoup. Good enough for descriptions.
_HTML_TAG = re.compile(r"<[^>]+>")


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
        description_raw = text("description")
        description = _HTML_TAG.sub("", description_raw).strip()
        guid = text("guid") or link or title

        contract = _guess_contract(title + " " + description)
        city = _extract_city(title)

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


def _guess_contract(text: str) -> ContractType:
    for pattern, contract in CONTRACT_PATTERNS:
        if pattern.search(text):
            return contract
    return ContractType.OTHER


def _extract_city(title: str) -> str:
    """HelloWork titles are usually `Job title - Contract - City`.

    Fall back to empty string if the pattern doesn't hold.
    """
    parts = [p.strip() for p in title.split(" - ")]
    if len(parts) >= 2:
        # Last segment is typically the location.
        candidate = parts[-1]
        # Strip trailing department code like "Paris (75)" → "Paris"
        candidate = re.sub(r"\s*\(\d+\)\s*$", "", candidate)
        return candidate
    return ""
