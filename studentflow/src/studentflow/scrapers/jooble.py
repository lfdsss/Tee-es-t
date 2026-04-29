"""Jooble scraper — official public JSON API.

Jooble aggregates millions of jobs across thousands of job boards worldwide.
Their API is free (single API key, no per-call cost on the hobby tier), uses
a simple POST-JSON schema, and complements France Travail / Adzuna / HelloWork
well because it indexes small French boards that the others miss.

Docs: https://jooble.org/api/about

Endpoint:
    POST https://jooble.org/api/{api_key}
    Body: { "keywords": "...", "location": "...", "page": "1" }

Response shape:
    {
        "totalCount": 123,
        "jobs": [
            {
                "title": "...",
                "location": "...",
                "snippet": "HTML-ish teaser",
                "salary": "...",
                "source": "indeed.fr",
                "type": "fulltime" | "parttime" | "contract" | None,
                "link": "https://...",
                "company": "...",
                "updated": "2026-04-10T12:00:00.0000000"
            }, ...
        ]
    }
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import ContractType, Offer, Source
from .base import BaseScraper

log = logging.getLogger(__name__)

BASE_URL = "https://jooble.org/api"

_HTML_TAG = re.compile(r"<[^>]+>")

# Same French-keyword priorities as the other scrapers, so contract detection
# stays consistent across sources.
_CONTRACT_KEYWORDS: list[tuple[re.Pattern[str], ContractType]] = [
    (re.compile(r"\b(alternance|apprentissage|apprenti)\b", re.I), ContractType.APPRENTICESHIP),
    (re.compile(r"\b(stage|stagiaire)\b", re.I), ContractType.INTERNSHIP),
    (re.compile(r"\b(freelance|indépendant|independant)\b", re.I), ContractType.FREELANCE),
    (re.compile(r"\bcdi\b", re.I), ContractType.CDI),
    (re.compile(r"\bcdd\b", re.I), ContractType.CDD),
]


def _guess_contract(title: str, snippet: str, job_type: str | None) -> ContractType:
    blob = f"{title} {snippet}"
    for pattern, contract in _CONTRACT_KEYWORDS:
        if pattern.search(blob):
            return contract
    jt = (job_type or "").lower()
    if jt == "parttime":
        return ContractType.PART_TIME
    if jt == "fulltime":
        return ContractType.CDI
    if jt == "contract":
        return ContractType.CDD
    return ContractType.OTHER


class JoobleScraper(BaseScraper):
    source = Source.JOOBLE

    def __init__(
        self,
        *,
        keyword: str = "etudiant",
        max_results: int = 50,
        location: str | None = None,
    ) -> None:
        self._keyword = keyword
        self._max_results = max_results
        self._location_override = location

    async def fetch(self) -> list[Offer]:
        settings = get_settings()
        if not settings.jooble_configured:
            log.info("Jooble not configured; skipping")
            return []

        location = self._location_override or settings.jooble_location
        async with httpx.AsyncClient(timeout=20.0) as client:
            rows = await self._search(client, settings.jooble_api_key, location)
        return [self._parse(row) for row in rows][: self._max_results]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _search(
        self, client: httpx.AsyncClient, api_key: str, location: str
    ) -> list[dict[str, Any]]:
        resp = await client.post(
            f"{BASE_URL}/{api_key}",
            json={"keywords": self._keyword, "location": location, "page": "1"},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("jobs", []) or []

    def _parse(self, row: dict[str, Any]) -> Offer:
        title = (row.get("title") or "").strip()
        snippet_raw = row.get("snippet") or ""
        snippet = _HTML_TAG.sub("", snippet_raw).strip()

        link = row.get("link") or ""
        # Jooble doesn't always expose a stable numeric id. Use the link as
        # the deterministic source_id so upserts remain idempotent.
        source_id = link or f"{title}|{row.get('company', '')}"

        contract = _guess_contract(title, snippet, row.get("type"))

        return Offer(
            source=Source.JOOBLE,
            source_id=source_id,
            title=title,
            description=snippet[:2000],
            company=row.get("company", "") or "",
            city=(row.get("location") or "").split(",")[0].strip(),
            remote=False,
            contract=contract,
            hours_per_week=None,
            skills=[],
            starts_on=_parse_dt(row.get("updated")),
            url=link,
        )


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        # Jooble timestamps can have 7 digits of fractional seconds which
        # fromisoformat rejects before 3.11. Trim to 6.
        trimmed = re.sub(r"\.(\d{6})\d*", r".\1", value)
        return datetime.fromisoformat(trimmed.replace("Z", "+00:00")).date()
    except ValueError:
        return None
