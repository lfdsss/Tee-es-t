"""Tests for the Indeed RSS scraper.

Uses `respx` to stub the RSS endpoint with a canned XML fixture.
Verifies: parsing, contract detection, city extraction, skill auto-extraction,
remote detection, max_results cap, error handling.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from studentflow.models import ContractType, Source
from studentflow.scrapers.indeed import (
    FEED_URL,
    IndeedScraper,
    _extract_city,
    _guess_contract,
)

CANNED_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Indeed - etudiant</title>
    <link>https://fr.indeed.com</link>
    <description>Jobs</description>
    <item>
      <title>Developpeur React junior - Stage - Paris</title>
      <link>https://fr.indeed.com/rc/clk?jk=abc1</link>
      <description>Stage React et TypeScript chez startup parisienne.</description>
      <pubDate>Mon, 01 Sep 2026 09:00:00 GMT</pubDate>
      <source url="https://acme.fr">Acme SAS</source>
      <guid>indeed-1</guid>
    </item>
    <item>
      <title>Community manager alternance - Lyon</title>
      <link>https://fr.indeed.com/rc/clk?jk=abc2</link>
      <description>Alternance. Animation Instagram, community management, Canva.</description>
      <pubDate>Tue, 02 Sep 2026 09:00:00 GMT</pubDate>
      <source url="https://example.fr">BigCorp</source>
      <guid>indeed-2</guid>
    </item>
    <item>
      <title>Vendeur temps partiel - Toulouse</title>
      <link>https://fr.indeed.com/rc/clk?jk=abc3</link>
      <description>Job etudiant, vente en boutique, caisse.</description>
      <pubDate>Wed, 03 Sep 2026 09:00:00 GMT</pubDate>
      <source url="https://shop.fr">Boutique</source>
      <guid>indeed-3</guid>
    </item>
    <item>
      <title>Dev Python remote</title>
      <link>https://fr.indeed.com/rc/clk?jk=abc4</link>
      <description>CDI full remote. Python, SQL, Docker.</description>
      <pubDate>Thu, 04 Sep 2026 09:00:00 GMT</pubDate>
      <source>RemoteCo</source>
      <guid>indeed-4</guid>
    </item>
    <item>
      <!-- Broken: no title -->
      <link>https://fr.indeed.com/rc/clk?jk=broken</link>
      <description>Missing title</description>
    </item>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_indeed_fetch_parses_canned_feed() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(FEED_URL).mock(return_value=httpx.Response(200, content=CANNED_RSS))

        offers = await IndeedScraper(keyword="etudiant", max_results=10).fetch()

    assert len(offers) == 4
    assert {o.source for o in offers} == {Source.INDEED}

    by_id = {o.source_id: o for o in offers}

    # Item 1: stage, Paris, skills auto-extracted
    stage = by_id["indeed-1"]
    assert stage.contract == ContractType.INTERNSHIP
    assert stage.city == "paris"
    assert stage.company == "Acme SAS"
    assert "react" in stage.skills
    assert "typescript" in stage.skills

    # Item 2: alternance, Lyon, community management skills
    alt = by_id["indeed-2"]
    assert alt.contract == ContractType.APPRENTICESHIP
    assert alt.city == "lyon"
    assert "community management" in alt.skills
    assert "canva" in alt.skills

    # Item 3: part_time, Toulouse, vente skills
    pt = by_id["indeed-3"]
    assert pt.contract == ContractType.PART_TIME
    assert pt.city == "toulouse"
    assert "vente" in pt.skills
    assert "caisse" in pt.skills

    # Item 4: CDI, remote detected
    cdi = by_id["indeed-4"]
    assert cdi.contract == ContractType.CDI
    assert cdi.remote is True
    assert "python" in cdi.skills
    assert "sql" in cdi.skills
    assert "docker" in cdi.skills


@pytest.mark.asyncio
async def test_indeed_respects_max_results() -> None:
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=CANNED_RSS))
        offers = await IndeedScraper(max_results=2).fetch()
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_indeed_handles_403() -> None:
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(403, content=b"Forbidden"))
        offers = await IndeedScraper().fetch()
    assert offers == []


@pytest.mark.asyncio
async def test_indeed_handles_invalid_xml() -> None:
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=b"not xml"))
        offers = await IndeedScraper().fetch()
    assert offers == []


def test_extract_city_from_title() -> None:
    assert _extract_city("Dev React - Acme - Paris (75)") == "Paris"
    assert _extract_city("Vendeur - Lyon") == "Lyon"
    assert _extract_city("No dash") == ""


def test_guess_contract_patterns() -> None:
    assert _guess_contract("stage de fin d'etudes") == ContractType.INTERNSHIP
    assert _guess_contract("contrat en alternance") == ContractType.APPRENTICESHIP
    assert _guess_contract("poste en CDI") == ContractType.CDI
    assert _guess_contract("job etudiant temps partiel") == ContractType.PART_TIME
    assert _guess_contract("aucun indicateur") == ContractType.OTHER
