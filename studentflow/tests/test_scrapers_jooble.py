"""Tests for the Jooble scraper."""

from __future__ import annotations

import httpx
import pytest
import respx

from studentflow.config import get_settings
from studentflow.models import ContractType, Source
from studentflow.scrapers.jooble import BASE_URL, JoobleScraper, _guess_contract

CANNED_RESPONSE = {
    "totalCount": 3,
    "jobs": [
        {
            "title": "Alternance Data Analyst",
            "location": "Paris, Île-de-France",
            "snippet": "<p>Rejoins notre <b>équipe data</b> en alternance.</p>",
            "salary": "",
            "source": "indeed.fr",
            "type": "fulltime",
            "link": "https://fr.jooble.org/desc/1",
            "company": "DataCorp",
            "updated": "2026-04-10T12:00:00.0000000",
        },
        {
            "title": "Vendeur boutique",
            "location": "Toulouse",
            "snippet": "Job étudiant week-end, 15h/semaine.",
            "type": "parttime",
            "link": "https://fr.jooble.org/desc/2",
            "company": "Boutique Centre",
            "updated": None,
        },
        {
            "title": "Ingenieur backend",
            "location": "Nantes, Pays de la Loire",
            "snippet": "CDI, poste confirme.",
            "type": "fulltime",
            "link": "https://fr.jooble.org/desc/3",
            "company": "Gamma",
            "updated": "2026-04-09T00:00:00",
        },
    ],
}


@pytest.fixture(autouse=True)
def _fake_jooble_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JOOBLE_API_KEY", "fake-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_jooble_fetch_parses_canned_response() -> None:
    with respx.mock:
        respx.post(f"{BASE_URL}/fake-key").mock(
            return_value=httpx.Response(200, json=CANNED_RESPONSE)
        )
        offers = await JoobleScraper(keyword="etudiant", max_results=10).fetch()

    assert len(offers) == 3
    assert all(o.source is Source.JOOBLE for o in offers)

    # Contracts inferred from French keywords + job_type fallback
    titles = [o.title for o in offers]
    contracts = {o.title: o.contract for o in offers}
    assert "Alternance Data Analyst" in titles
    assert contracts["Alternance Data Analyst"] == ContractType.APPRENTICESHIP
    assert contracts["Vendeur boutique"] == ContractType.PART_TIME
    assert contracts["Ingenieur backend"] == ContractType.CDI

    # HTML stripped + city first segment + link reused as source_id
    alt = next(o for o in offers if o.title.startswith("Alternance"))
    assert "<b>" not in alt.description
    assert alt.city == "paris"
    assert alt.source_id == "https://fr.jooble.org/desc/1"
    assert alt.company == "DataCorp"


@pytest.mark.asyncio
async def test_jooble_respects_max_results() -> None:
    with respx.mock:
        respx.post(f"{BASE_URL}/fake-key").mock(
            return_value=httpx.Response(200, json=CANNED_RESPONSE)
        )
        offers = await JoobleScraper(max_results=2).fetch()
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_jooble_empty_jobs() -> None:
    with respx.mock:
        respx.post(f"{BASE_URL}/fake-key").mock(return_value=httpx.Response(200, json={"jobs": []}))
        offers = await JoobleScraper().fetch()
    assert offers == []


@pytest.mark.asyncio
async def test_jooble_skips_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JOOBLE_API_KEY", raising=False)
    get_settings.cache_clear()
    # No respx mock: a network call would raise.
    offers = await JoobleScraper().fetch()
    assert offers == []


def test_guess_contract_keywords_take_precedence() -> None:
    assert (
        _guess_contract("Stage développeur", "Stage de 6 mois", "fulltime")
        == ContractType.INTERNSHIP
    )
    assert _guess_contract("Dev senior", "", "fulltime") == ContractType.CDI
    assert _guess_contract("Dev", "", "parttime") == ContractType.PART_TIME
    assert _guess_contract("Dev", "", "contract") == ContractType.CDD
    assert _guess_contract("Dev", "", None) == ContractType.OTHER
