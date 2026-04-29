"""France Travail (ex Pôle Emploi) scraper.

Uses the official public API:
  - OAuth2 token: POST entreprise.francetravail.fr/connexion/oauth2/access_token
  - Offers search: GET api.francetravail.io/partenaire/offresdemploi/v2/offres/search

Requires `FRANCE_TRAVAIL_CLIENT_ID` and `FRANCE_TRAVAIL_CLIENT_SECRET` in env.
Docs: https://francetravail.io/data/api/offres-emploi
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import ContractType, Offer, Source
from .base import BaseScraper

log = logging.getLogger(__name__)

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
SCOPE = "api_offresdemploiv2 o2dsoffre"

# Map FT contract codes to our enum.
CONTRACT_MAP: dict[str, ContractType] = {
    "CDI": ContractType.CDI,
    "CDD": ContractType.CDD,
    "MIS": ContractType.CDD,  # mission intérim
    "SAI": ContractType.CDD,  # saisonnier
    "CCE": ContractType.APPRENTICESHIP,  # contrat aidé
    "DIN": ContractType.FREELANCE,
    "FRA": ContractType.FREELANCE,
    "LIB": ContractType.FREELANCE,
}


class FranceTravailScraper(BaseScraper):
    source = Source.FRANCE_TRAVAIL

    def __init__(self, *, keyword: str = "étudiant", max_results: int = 50) -> None:
        self._keyword = keyword
        self._max_results = max_results
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    async def fetch(self) -> list[Offer]:
        settings = get_settings()
        if not settings.france_travail_configured:
            log.info("France Travail not configured; skipping")
            return []

        async with httpx.AsyncClient(timeout=20.0) as client:
            token = await self._get_token(
                client, settings.france_travail_client_id, settings.france_travail_client_secret
            )
            raw = await self._search(client, token)
        return [self._parse(row) for row in raw]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _get_token(
        self, client: httpx.AsyncClient, client_id: str, client_secret: str
    ) -> str:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _search(self, client: httpx.AsyncClient, token: str) -> list[dict[str, Any]]:
        params = {
            "motsCles": self._keyword,
            "range": f"0-{max(0, self._max_results - 1)}",
        }
        resp = await client.get(
            SEARCH_URL,
            params=params,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        # 204 means "no content" (valid).
        if resp.status_code == 204:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("resultats", [])

    def _parse(self, row: dict[str, Any]) -> Offer:
        contract_code = (row.get("typeContrat") or "").upper()
        contract = CONTRACT_MAP.get(contract_code, ContractType.OTHER)

        lieu = row.get("lieuTravail") or {}
        city = (lieu.get("libelle") or "").split("-")[-1].strip()

        # Parse dates (format: "2024-09-01T00:00:00.000+02:00")
        starts_on = _parse_date(row.get("dateActualisation"))

        skills = []
        for comp in row.get("competences", []) or []:
            lib = comp.get("libelle")
            if lib:
                skills.append(lib)
        # langues + qualitesProfessionnelles ignored for now — can enrich later.

        hours = None
        duree_hebdo = row.get("dureeTravailLibelle") or ""
        if "h" in duree_hebdo.lower():
            digits = "".join(c for c in duree_hebdo if c.isdigit())
            if digits:
                try:
                    hours = int(digits[:2])
                except ValueError:
                    hours = None

        return Offer(
            source=Source.FRANCE_TRAVAIL,
            source_id=str(row.get("id", "")),
            title=row.get("intitule", ""),
            description=row.get("description", "") or "",
            company=(row.get("entreprise") or {}).get("nom", "") or "",
            city=city,
            remote=False,  # France Travail doesn't flag remote reliably
            contract=contract,
            hours_per_week=hours,
            skills=skills,
            starts_on=starts_on,
            url=row.get("origineOffre", {}).get("urlOrigine", "") or "",
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None
