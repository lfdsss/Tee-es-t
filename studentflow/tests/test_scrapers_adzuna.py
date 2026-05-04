"""Tests for the Adzuna scraper.

The scraper hits the public Adzuna REST API, which returns JSON. We stub the
endpoint with `respx` and assert that parsing handles:
  - the nominal shape (city/company/contract inference)
  - missing fields (defensive)
  - contract inference via French keywords taking precedence over the generic
    `contract_type` / `contract_time` fields
  - the `adzuna_configured` gate (no creds → empty list, no HTTP call)
"""

from __future__ import annotations

import httpx
import pytest
import respx

from studentflow.config import get_settings
from studentflow.models import ContractType, Source
from studentflow.scrapers.adzuna import BASE_URL, AdzunaScraper, _guess_contract

CANNED_RESPONSE = {
    "count": 4,
    "results": [
        {
            "id": "adz-1",
            "title": "Alternance développeur Python",
            "description": "Rejoins notre equipe en alternance sur Paris.",
            "company": {"display_name": "Acme SAS"},
            "location": {"display_name": "Paris, Île-de-France, France"},
            "redirect_url": "https://www.adzuna.fr/land/ad/1",
            "contract_type": "contract",
            "contract_time": "full_time",
            "created": "2026-04-01T09:00:00Z",
        },
        {
            "id": "adz-2",
            "title": "Stage marketing",
            "description": "Stage de 6 mois en marketing digital.",
            "company": {"display_name": "BetaCorp"},
            "location": {"display_name": "Lyon, Auvergne-Rhône-Alpes, France"},
            "redirect_url": "https://www.adzuna.fr/land/ad/2",
            "contract_type": "contract",
            "contract_time": "full_time",
            "created": "2026-04-02T09:00:00Z",
        },
        {
            "id": "adz-3",
            "title": "Ingenieur backend senior",
            "description": "Poste en CDI.",
            "company": {"display_name": "Gamma"},
            "location": {"display_name": "Nantes, Pays de la Loire, France"},
            "redirect_url": "https://www.adzuna.fr/land/ad/3",
            "contract_type": "permanent",
            "contract_time": "full_time",
            "created": "2026-04-03T09:00:00Z",
        },
        {
            "id": "adz-4",
            "title": "Vendeur boutique",
            "description": "Job etudiant week-end.",
            "company": {},  # missing company — must not crash
            "location": {"display_name": "Toulouse"},
            "redirect_url": "",
            "contract_type": "contract",
            "contract_time": "part_time",
            "created": None,
        },
    ],
}


@pytest.fixture(autouse=True)
def _fake_adzuna_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `adzuna_configured` return True for every test in this module."""
    monkeypatch.setenv("ADZUNA_APP_ID", "fake-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_adzuna_fetch_parses_canned_response() -> None:
    with respx.mock:
        respx.get(f"{BASE_URL}/fr/search/1").mock(
            return_value=httpx.Response(200, json=CANNED_RESPONSE)
        )
        offers = await AdzunaScraper(keyword="etudiant", max_results=10).fetch()

    assert len(offers) == 4
    assert all(o.source is Source.ADZUNA for o in offers)

    by_id = {o.source_id: o for o in offers}

    # Item 1: "alternance" in title → APPRENTICESHIP (wins over contract_type)
    assert by_id["adz-1"].contract == ContractType.APPRENTICESHIP
    assert by_id["adz-1"].city == "paris"
    assert by_id["adz-1"].company == "Acme SAS"

    # Item 2: "stage" in title → INTERNSHIP (wins over contract_type)
    assert by_id["adz-2"].contract == ContractType.INTERNSHIP
    assert by_id["adz-2"].city == "lyon"

    # Item 3: permanent → CDI
    assert by_id["adz-3"].contract == ContractType.CDI
    assert by_id["adz-3"].city == "nantes"

    # Item 4: missing company handled, part_time → PART_TIME
    assert by_id["adz-4"].company == ""
    assert by_id["adz-4"].contract == ContractType.PART_TIME
    assert by_id["adz-4"].city == "toulouse"


@pytest.mark.asyncio
async def test_adzuna_respects_max_results() -> None:
    with respx.mock:
        respx.get(f"{BASE_URL}/fr/search/1").mock(
            return_value=httpx.Response(200, json=CANNED_RESPONSE)
        )
        offers = await AdzunaScraper(max_results=2).fetch()
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_adzuna_empty_results() -> None:
    with respx.mock:
        respx.get(f"{BASE_URL}/fr/search/1").mock(
            return_value=httpx.Response(200, json={"results": []})
        )
        offers = await AdzunaScraper().fetch()
    assert offers == []


@pytest.mark.asyncio
async def test_adzuna_skips_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear the creds installed by the autouse fixture.
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    get_settings.cache_clear()

    # No respx mock: if the scraper tries to call HTTP, the test fails.
    offers = await AdzunaScraper().fetch()
    assert offers == []


def test_guess_contract_french_keywords_win_over_generic_fields() -> None:
    # "alternance" should beat contract_type=permanent
    row = {
        "title": "Alternance dev",
        "description": "",
        "contract_type": "permanent",
        "contract_time": "full_time",
    }
    assert _guess_contract(row) == ContractType.APPRENTICESHIP


def test_guess_contract_falls_back_to_contract_type() -> None:
    row = {"title": "Software engineer", "description": "", "contract_type": "permanent"}
    assert _guess_contract(row) == ContractType.CDI

    row = {"title": "Temporary role", "description": "", "contract_type": "contract"}
    assert _guess_contract(row) == ContractType.CDD


def test_guess_contract_other_when_nothing_matches() -> None:
    assert _guess_contract({"title": "", "description": ""}) == ContractType.OTHER
