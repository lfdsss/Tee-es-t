"""France Travail (ex Pôle Emploi) scraper.

Uses the official public API:
  - OAuth2 token: POST entreprise.francetravail.fr/connexion/oauth2/access_token
  - Offers search: GET api.francetravail.io/partenaire/offresdemploi/v2/offres/search

Requires `FRANCE_TRAVAIL_CLIENT_ID` and `FRANCE_TRAVAIL_CLIENT_SECRET` in env.
Docs: https://francetravail.io/data/api/offres-emploi
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import ContractType, Offer, SalaryPeriod, Source
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

        salaire = row.get("salaire") or {}
        salary_min, salary_max, salary_period = _parse_salary(salaire.get("libelle") or "")

        # France Travail doesn't ship an expiration field, but offers go stale
        # within ~30 days of the last actualisation. Use that as a soft floor
        # so the MatcherAgent stops pushing notifs on dead listings.
        expires_at = _parse_datetime(row.get("dateActualisation"))
        if expires_at is not None:
            expires_at = expires_at + timedelta(days=30)

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
            salary_min=salary_min,
            salary_max=salary_max,
            salary_period=salary_period,
            expires_at=expires_at,
            url=row.get("origineOffre", {}).get("urlOrigine", "") or "",
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    # Drop timezone — Offer.expires_at is naive UTC like scraped_at.
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


# Regexes for the most common France Travail salary libellés. We do best-effort
# parsing — if none match, (None, None, None) is returned and the offer keeps
# salary fields null. Examples we handle:
#   "Mensuel de 1 800,00 Euros à 2 200,00 Euros sur 12 mois"
#   "Horaire de 11,52 € à 14,00 €"
#   "Annuel de 30000,00 Euros sur 12 mois"
#   "Mensuel de 2000 Euros"
_NUM = r"(\d+(?:[ .]?\d{3})*(?:,\d+)?)"  # captures "1 800,00", "30000,00", "11,52"
_RANGE_RE = re.compile(
    rf"\b(Horaire|Mensuel|Annuel)\s+de\s+{_NUM}\s*(?:€|Euros?)\s*(?:à|a)\s+{_NUM}\s*(?:€|Euros?)",
    re.IGNORECASE,
)
_SINGLE_RE = re.compile(
    rf"\b(Horaire|Mensuel|Annuel)\s+de\s+{_NUM}\s*(?:€|Euros?)",
    re.IGNORECASE,
)


def _to_float(raw: str) -> float | None:
    cleaned = raw.replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _resolve_period(label: str, amount: float | None) -> tuple[SalaryPeriod | None, float | None]:
    """Map a FT libellé prefix ('Horaire'/'Mensuel'/'Annuel') to our enum.

    Annual figures are folded down to monthly so the matcher can compare them
    on the same axis as MONTHLY salaries. HOURLY stays HOURLY.
    """
    label = label.lower()
    if label == "horaire":
        return SalaryPeriod.HOURLY, amount
    if label == "mensuel":
        return SalaryPeriod.MONTHLY, amount
    if label == "annuel":
        return SalaryPeriod.MONTHLY, (amount / 12 if amount is not None else None)
    return None, None


def _parse_salary(libelle: str) -> tuple[float | None, float | None, SalaryPeriod | None]:
    if not libelle:
        return None, None, None

    m = _RANGE_RE.search(libelle)
    if m:
        period, lo = _resolve_period(m.group(1), _to_float(m.group(2)))
        _, hi = _resolve_period(m.group(1), _to_float(m.group(3)))
        if period and lo is not None and hi is not None:
            return lo, hi, period

    m = _SINGLE_RE.search(libelle)
    if m:
        period, amount = _resolve_period(m.group(1), _to_float(m.group(2)))
        if period and amount is not None:
            return amount, None, period

    return None, None, None
