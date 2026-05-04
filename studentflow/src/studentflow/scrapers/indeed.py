"""Indeed scraper via public RSS feed.

Indeed still serves RSS 2.0 feeds for search queries on most country domains.
No API key required — we just hit the feed URL, parse XML, and map to Offer.

Feed URL pattern:
    https://fr.indeed.com/rss?q={keyword}&l={location}&sort=date

Item shape:
    <item>
      <title>Job Title - Company - City</title>
      <link>https://fr.indeed.com/rc/clk?...</link>
      <description>HTML snippet</description>
      <pubDate>Wed, 09 Apr 2026 12:00:00 GMT</pubDate>
      <source url="...">Company Name</source>
    </item>

If Indeed blocks or returns an error (403/captcha), we gracefully return [].
The ScraperAgent's isolation guarantees the other scrapers keep running.

We auto-enrich skills from the description using the same deterministic
vocabulary matcher used elsewhere, so the matching engine gets Jaccard
scores even from sources with no structured skill tags.
"""

from __future__ import annotations

import contextlib
import logging
import re
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

from ..models import ContractType, Offer, Source
from ..utils.skills import extract_skills
from .base import BaseScraper

log = logging.getLogger(__name__)

FEED_URL = "https://fr.indeed.com/rss"
USER_AGENT = "StudentFlow/0.1 (+https://github.com/them311/Tee-es-t)"

_CONTRACT_PATTERNS: list[tuple[re.Pattern[str], ContractType]] = [
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

_HTML_TAG = re.compile(r"<[^>]+>")


class IndeedScraper(BaseScraper):
    source = Source.INDEED

    def __init__(
        self,
        *,
        keyword: str = "etudiant",
        location: str = "France",
        max_results: int = 50,
    ) -> None:
        self._keyword = keyword
        self._location = location
        self._max_results = max_results

    async def fetch(self) -> list[Offer]:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        ) as client:
            xml = await self._fetch_feed(client)
        if xml is None:
            return []
        return self._parse(xml)[: self._max_results]

    async def _fetch_feed(self, client: httpx.AsyncClient) -> bytes | None:
        try:
            resp = await client.get(
                FEED_URL,
                params={"q": self._keyword, "l": self._location, "sort": "date"},
            )
            if resp.status_code in (403, 429, 503):
                log.warning(
                    "Indeed returned %d — rate-limited or geo-blocked",
                    resp.status_code,
                )
                return None
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPError as exc:
            log.warning("Indeed feed fetch failed: %s", exc)
            return None

    def _parse(self, xml: bytes) -> list[Offer]:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            log.warning("Indeed: RSS parse error: %s", exc)
            return []

        items = root.findall(".//item")
        offers: list[Offer] = []
        for item in items:
            try:
                offer = self._parse_item(item)
            except Exception as exc:
                log.warning("Indeed: failed to parse item: %s", exc)
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

        # Indeed <source> tag contains the company name.
        source_el = item.find("source")
        company = (source_el.text or "").strip() if source_el is not None else ""

        contract = _guess_contract(title + " " + description)
        city = _extract_city(title)

        starts_on = None
        pub_date = text("pubDate")
        if pub_date:
            with contextlib.suppress(Exception):
                starts_on = parsedate_to_datetime(pub_date).date()

        skills = extract_skills(f"{title}\n{description}")

        return Offer(
            source=Source.INDEED,
            source_id=guid,
            title=title,
            description=description[:2000],
            company=company,
            city=city,
            remote="télétravail" in (title + description).lower()
            or "remote" in (title + description).lower(),
            contract=contract,
            skills=skills,
            starts_on=starts_on,
            url=link,
        )


def _guess_contract(text: str) -> ContractType:
    for pattern, contract in _CONTRACT_PATTERNS:
        if pattern.search(text):
            return contract
    return ContractType.OTHER


def _extract_city(title: str) -> str:
    """Indeed titles are usually 'Job Title - Company - City (Dept)'.

    Try the last segment after ' - '.
    """
    parts = [p.strip() for p in title.split(" - ")]
    if len(parts) >= 2:
        candidate = parts[-1]
        candidate = re.sub(r"\s*\(\d+\)\s*$", "", candidate)
        return candidate
    return ""
