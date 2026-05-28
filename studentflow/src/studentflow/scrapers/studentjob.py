"""StudentJob.fr scraper via Jobster public API.

StudentJob.fr uses Jobster (jobs.platform.jobster.com) as their search backend.
The platform exposes a public `/serve` endpoint that returns JSON offer listings
without authentication. We reproduce the exact request the browser SDK makes.

Fallback chain:
  1. Jobster /serve API (primary — JSON, structured, paginated)
  2. StudentJob RSS feed (secondary — less structured but reliable)
  3. Return [] gracefully (never crash the ScraperAgent loop)

Anti-bot notes:
  - Jobster checks the Referer header: must be studentjob.fr
  - Requires a realistic User-Agent (Chrome/Windows)
  - No session cookie required for the listing endpoint
  - Rate limit: ~10 req/min per IP (we stay well below with 15-min intervals)
"""

from __future__ import annotations

import logging
import re
from datetime import date
from xml.etree import ElementTree as ET

import httpx

from ..models import ContractType, Offer, Source
from ..utils.skills import extract_skills
from .base import BaseScraper

log = logging.getLogger(__name__)

# Jobster serve endpoint — same as what studentjob.fr's browser SDK calls.
JOBSTER_URL = "https://jobs.platform.jobster.com/serve"
JOBSTER_PUBLISHER_HASH = "75e9ab8212326b9b6ef449c64ce1d5cbdb10fe72"

# RSS fallback — StudentJob.fr exposes a public Atom/RSS feed.
RSS_URL = "https://www.studentjob.fr/rss/jobs"
RSS_URL_ALT = "https://www.studentjob.fr/rss"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_CONTRACT_PATTERNS: list[tuple[re.Pattern[str], ContractType]] = [
    (re.compile(r"\b(stage|stagiaire|intern)\b", re.I), ContractType.INTERNSHIP),
    (re.compile(r"\b(alternance|apprentissage|apprenti)\b", re.I), ContractType.APPRENTICESHIP),
    (re.compile(r"\bcdi\b", re.I), ContractType.CDI),
    (re.compile(r"\bcdd\b", re.I), ContractType.CDD),
    (re.compile(r"\b(temps partiel|part.?time|week.?end|job étudiant)\b", re.I), ContractType.PART_TIME),
    (re.compile(r"\b(freelance|indépendant|independant)\b", re.I), ContractType.FREELANCE),
]

_HTML_TAG = re.compile(r"<[^>]+>")


class StudentJobScraper(BaseScraper):
    source = Source.STUDENTJOB

    def __init__(self, *, max_results: int = 50) -> None:
        self._max_results = max_results

    async def fetch(self) -> list[Offer]:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Referer": "https://www.studentjob.fr/",
                "Origin": "https://www.studentjob.fr",
            },
        ) as client:
            # Try Jobster API first.
            offers = await self._fetch_jobster(client)
            if offers:
                log.info("StudentJobScraper (Jobster): %d offers", len(offers))
                return offers[: self._max_results]

            # Fallback: RSS feed.
            offers = await self._fetch_rss(client)
            if offers:
                log.info("StudentJobScraper (RSS fallback): %d offers", len(offers))
                return offers[: self._max_results]

        log.info("StudentJobScraper: both sources returned empty, skipping")
        return []

    # ---- Jobster /serve ----

    async def _fetch_jobster(self, client: httpx.AsyncClient) -> list[Offer]:
        """Call the Jobster platform API that StudentJob.fr's frontend uses."""
        payload = {
            "publisherHash": JOBSTER_PUBLISHER_HASH,
            "query": "etudiant",
            "page": 1,
            "pageSize": min(self._max_results, 50),
            "country": "fr",
        }
        try:
            resp = await client.post(JOBSTER_URL, json=payload)
            if resp.status_code in (403, 429, 503, 521, 522, 524):
                log.warning("Jobster returned %d (blocked/rate-limited)", resp.status_code)
                return []
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("Jobster fetch failed: %s", exc)
            return []

        jobs = data.get("jobs") or data.get("results") or data.get("data") or []
        if not isinstance(jobs, list):
            log.warning("Jobster: unexpected response shape — keys: %s", list(data.keys()))
            return []

        offers: list[Offer] = []
        for job in jobs:
            try:
                offer = self._parse_jobster_item(job)
                if offer:
                    offers.append(offer)
            except Exception as exc:
                log.debug("Jobster: failed to parse job: %s", exc)
        return offers

    def _parse_jobster_item(self, job: dict) -> Offer | None:
        title = (job.get("title") or job.get("name") or "").strip()
        if not title:
            return None

        company = (job.get("company") or job.get("employer") or "").strip()
        city = (job.get("city") or job.get("location") or job.get("locality") or "").strip()
        description = _HTML_TAG.sub(
            "", (job.get("description") or job.get("body") or "")
        ).strip()
        url = (job.get("url") or job.get("link") or job.get("applyUrl") or "").strip()
        job_id = str(job.get("id") or job.get("jobId") or url or title)

        contract_raw = job.get("contractType") or job.get("contract") or ""
        contract = _guess_contract(f"{title} {contract_raw} {description}")

        remote = any(
            kw in (title + description).lower()
            for kw in ("télétravail", "remote", "distanciel")
        )

        skills = extract_skills(f"{title}\n{description}")

        hours = None
        hours_raw = job.get("hoursPerWeek") or job.get("hours") or ""
        if hours_raw:
            digits = re.findall(r"\d+", str(hours_raw))
            if digits:
                hours = int(digits[0])

        return Offer(
            source=Source.STUDENTJOB,
            source_id=f"jobster:{job_id}",
            title=title,
            description=description[:2000],
            company=company,
            city=city,
            remote=remote,
            contract=contract,
            hours_per_week=hours,
            skills=skills,
            url=url,
        )

    # ---- RSS fallback ----

    async def _fetch_rss(self, client: httpx.AsyncClient) -> list[Offer]:
        for url in (RSS_URL, RSS_URL_ALT):
            try:
                resp = await client.get(
                    url,
                    headers={
                        "Accept": "application/rss+xml, application/xml, text/xml, */*"
                    },
                )
                if resp.status_code in (403, 404, 429):
                    continue
                resp.raise_for_status()
                return self._parse_rss(resp.content)
            except (httpx.HTTPError, Exception) as exc:
                log.debug("StudentJob RSS %s failed: %s", url, exc)
        return []

    def _parse_rss(self, xml_bytes: bytes) -> list[Offer]:
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            log.warning("StudentJob RSS parse error: %s", exc)
            return []

        items = root.findall(".//item") or root.findall(".//entry")
        offers: list[Offer] = []
        for item in items:
            try:
                offer = self._parse_rss_item(item)
                if offer:
                    offers.append(offer)
            except Exception as exc:
                log.debug("StudentJob RSS item parse error: %s", exc)
        return offers

    def _parse_rss_item(self, item: ET.Element) -> Offer | None:
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        def text(tag: str) -> str:
            # Try plain tag first, then with atom namespace.
            el = item.find(tag) or item.find(f"atom:{tag}", ns)
            return (el.text or "").strip() if el is not None else ""

        title = text("title")
        if not title:
            return None

        link = text("link")
        if not link:
            link_el = item.find("link")
            if link_el is not None:
                link = link_el.get("href", "") or link_el.text or ""

        guid = text("guid") or text("id") or link or title
        description_raw = text("description") or text("summary") or text("content")
        description = _HTML_TAG.sub("", description_raw).strip()

        contract = _guess_contract(title + " " + description)
        city = _extract_city_from_title(title)
        skills = extract_skills(f"{title}\n{description}")
        remote = "télétravail" in (title + description).lower()

        return Offer(
            source=Source.STUDENTJOB,
            source_id=f"rss:{guid}",
            title=title,
            description=description[:2000],
            company="",
            city=city,
            remote=remote,
            contract=contract,
            skills=skills,
            url=link,
        )


def _guess_contract(text: str) -> ContractType:
    for pattern, contract in _CONTRACT_PATTERNS:
        if pattern.search(text):
            return contract
    return ContractType.PART_TIME  # default for StudentJob = part-time student jobs


def _extract_city_from_title(title: str) -> str:
    """Try to extract a city from a job title using common patterns."""
    parts = [p.strip() for p in title.split(" - ")]
    if len(parts) >= 2:
        candidate = parts[-1]
        candidate = re.sub(r"\s*\(\d+\)\s*$", "", candidate)
        if len(candidate) < 40:
            return candidate
    # Try "à {city}" pattern.
    m = re.search(r"\bà\s+([A-ZÀ-Ÿ][a-zA-ZÀ-ÿ\-]+(?:\s+[a-zA-ZÀ-ÿ\-]+)?)", title)
    if m:
        return m.group(1)
    return ""
