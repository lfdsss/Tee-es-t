"""Adzuna scraper — official public JSON API.

Adzuna exposes a clean, free-tier REST API (1000 calls/month on the free plan).
We treat it as a third reliable source alongside France Travail (FR-only) and
HelloWork (RSS). Adzuna is useful because:

  - It's multi-country (fr, gb, us, de…) so we can scale beyond France later.
  - The schema is stable and well documented.
  - It does not require OAuth — just app_id + app_key query params.

Docs: https://developer.adzuna.com/activedocs

Endpoint:
    GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
        ?app_id=...&app_key=...&what=...&results_per_page=...&content-type=application/json

Rate limits: soft, ~1 req/s is safe.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import ContractType, Offer, Source
from .base import BaseScraper

log = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_RESULTS_PER_PAGE = 50  # Adzuna caps at 50


# Adzuna uses `contract_type` ∈ {permanent, contract} and
# `contract_time` ∈ {full_time, part_time, None}. Neither maps cleanly to the
# French contract landscape, so we infer from the combination.
def _guess_contract(row: dict[str, Any]) -> ContractType:
    ctype = (row.get("contract_type") or "").lower()
    ctime = (row.get("contract_time") or "").lower()
    title = (row.get("title") or "").lower()
    desc = (row.get("description") or "").lower()
    blob = f"{title} {desc}"

    # French-specific keywords take precedence (Adzuna indexes French offers).
    if "alternance" in blob or "apprentissage" in blob or "apprenti" in blob:
        return ContractType.APPRENTICESHIP
    if "stage" in blob or "stagiaire" in blob:
        return ContractType.INTERNSHIP
    if "freelance" in blob or "indépendant" in blob or "independant" in blob:
        return ContractType.FREELANCE
    # Part-time is more informative than the permanent/contract axis in the
    # French student-job context, so check it first.
    if ctime == "part_time":
        return ContractType.PART_TIME
    if ctype == "permanent":
        return ContractType.CDI
    if ctype == "contract":
        return ContractType.CDD
    return ContractType.OTHER


class AdzunaScraper(BaseScraper):
    source = Source.ADZUNA

    def __init__(
        self,
        *,
        keyword: str = "etudiant",
        max_results: int = 50,
        country: str | None = None,
    ) -> None:
        self._keyword = keyword
        self._max_results = max_results
        self._country_override = country

    async def fetch(self) -> list[Offer]:
        settings = get_settings()
        if not settings.adzuna_configured:
            log.info("Adzuna not configured; skipping")
            return []

        country = self._country_override or settings.adzuna_country
        async with httpx.AsyncClient(timeout=20.0) as client:
            rows = await self._search(
                client,
                country=country,
                app_id=settings.adzuna_app_id,
                app_key=settings.adzuna_app_key,
            )
        return [self._parse(row) for row in rows][: self._max_results]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _search(
        self,
        client: httpx.AsyncClient,
        *,
        country: str,
        app_id: str,
        app_key: str,
    ) -> list[dict[str, Any]]:
        url = f"{BASE_URL}/{country}/search/1"
        resp = await client.get(
            url,
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": self._keyword,
                "results_per_page": min(self._max_results, DEFAULT_RESULTS_PER_PAGE),
                "content-type": "application/json",
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", []) or []

    def _parse(self, row: dict[str, Any]) -> Offer:
        location = row.get("location") or {}
        # Adzuna returns a display_name like "Paris, Île-de-France, France";
        # take the first segment as the city.
        city_raw = (location.get("display_name") or "").split(",")[0].strip()

        company = (row.get("company") or {}).get("display_name", "") or ""

        created = _parse_dt(row.get("created"))

        contract = _guess_contract(row)

        return Offer(
            source=Source.ADZUNA,
            source_id=str(row.get("id", "")),
            title=row.get("title", "") or "",
            description=(row.get("description") or "")[:2000],
            company=company,
            city=city_raw,
            remote=False,  # Adzuna does not flag remote reliably
            contract=contract,
            hours_per_week=None,
            skills=[],  # Adzuna does not expose structured skills
            starts_on=created,
            url=row.get("redirect_url", "") or "",
        )


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None
