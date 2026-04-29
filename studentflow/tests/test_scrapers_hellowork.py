"""Tests for the HelloWork RSS scraper.

Uses `respx` to stub the RSS endpoint with a canned XML fixture. We keep the
fixture small but representative: multiple items, mixed contracts, a broken
item that must be skipped, a city with a department code, and an HTML blob in
the description.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from studentflow.models import ContractType, Source
from studentflow.scrapers.hellowork import (
    FEED_URL,
    HelloWorkScraper,
    _extract_city,
    _guess_contract,
)

CANNED_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>HelloWork - etudiant</title>
    <link>https://www.hellowork.com/</link>
    <description>Offres</description>
    <item>
      <title>Developpeur React - Stage - Paris (75)</title>
      <link>https://www.hellowork.com/fr-fr/emploi/1.html</link>
      <description><![CDATA[<p>Stage de <b>6 mois</b> en plein Paris.</p>]]></description>
      <pubDate>Mon, 01 Sep 2026 09:00:00 +0200</pubDate>
      <guid isPermaLink="false">hw-1</guid>
    </item>
    <item>
      <title>Alternant marketing digital - Alternance - Lyon (69)</title>
      <link>https://www.hellowork.com/fr-fr/emploi/2.html</link>
      <description>Rejoins notre equipe en alternance, teletravail partiel possible.</description>
      <pubDate>Tue, 02 Sep 2026 09:00:00 +0200</pubDate>
      <guid>hw-2</guid>
    </item>
    <item>
      <title>Vendeur week-end - Temps partiel - Toulouse</title>
      <link>https://www.hellowork.com/fr-fr/emploi/3.html</link>
      <description>Job etudiant en boutique.</description>
      <pubDate>Wed, 03 Sep 2026 09:00:00 +0200</pubDate>
      <guid>hw-3</guid>
    </item>
    <item>
      <title>Ingenieur backend - CDI - Nantes</title>
      <link>https://www.hellowork.com/fr-fr/emploi/4.html</link>
      <description>Poste en CDI.</description>
      <pubDate>Thu, 04 Sep 2026 09:00:00 +0200</pubDate>
      <guid>hw-4</guid>
    </item>
    <item>
      <!-- Broken item: no title, must be skipped gracefully -->
      <link>https://www.hellowork.com/fr-fr/emploi/5.html</link>
      <description>Pas de titre.</description>
    </item>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_hellowork_fetch_parses_canned_feed() -> None:
    with respx.mock(assert_all_called=True) as mock:
        mock.get(FEED_URL).mock(return_value=httpx.Response(200, content=CANNED_RSS))

        offers = await HelloWorkScraper(keyword="etudiant", max_results=10).fetch()

    # 5 items, 1 broken without title → 4 valid
    assert len(offers) == 4
    assert {o.source for o in offers} == {Source.HELLOWORK}

    by_id = {o.source_id: o for o in offers}

    # Item 1: stage + city with department code stripped (model lowercases city)
    stage = by_id["hw-1"]
    assert stage.contract == ContractType.INTERNSHIP
    assert stage.city == "paris"
    assert stage.title.startswith("Developpeur React")
    # Description HTML tags are stripped
    assert "<b>" not in stage.description
    assert "6 mois" in stage.description

    # Item 2: alternance + Lyon
    alt = by_id["hw-2"]
    assert alt.contract == ContractType.APPRENTICESHIP
    assert alt.city == "lyon"

    # Item 3: part-time (week-end)
    pt = by_id["hw-3"]
    assert pt.contract == ContractType.PART_TIME
    assert pt.city == "toulouse"

    # Item 4: CDI
    cdi = by_id["hw-4"]
    assert cdi.contract == ContractType.CDI
    assert cdi.city == "nantes"


@pytest.mark.asyncio
async def test_hellowork_respects_max_results() -> None:
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=CANNED_RSS))
        offers = await HelloWorkScraper(max_results=2).fetch()
    assert len(offers) == 2


@pytest.mark.asyncio
async def test_hellowork_handles_invalid_xml() -> None:
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=b"not xml at all"))
        offers = await HelloWorkScraper().fetch()
    assert offers == []


@pytest.mark.asyncio
async def test_hellowork_handles_empty_channel() -> None:
    empty = b"""<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>"""
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, content=empty))
        offers = await HelloWorkScraper().fetch()
    assert offers == []


def test_extract_city_strips_department_code() -> None:
    assert _extract_city("Dev React - Stage - Paris (75)") == "Paris"
    assert _extract_city("Dev React - Stage - Lyon") == "Lyon"
    assert _extract_city("Weird single segment") == ""


def test_guess_contract_patterns() -> None:
    assert _guess_contract("poste en CDI à pourvoir") == ContractType.CDI
    assert _guess_contract("stage de fin d'études") == ContractType.INTERNSHIP
    assert _guess_contract("contrat en alternance 2 ans") == ContractType.APPRENTICESHIP
    assert _guess_contract("mission freelance") == ContractType.FREELANCE
    assert _guess_contract("job étudiant week-end") == ContractType.PART_TIME
    assert _guess_contract("aucun indicateur ici") == ContractType.OTHER
