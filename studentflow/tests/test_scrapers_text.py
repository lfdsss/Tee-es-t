"""Direct unit tests for `studentflow.scrapers._text`.

Existing per-scraper tests cover the helpers indirectly via real RSS fixtures.
This file is the canonical test surface for the helpers themselves: edge cases
that don't naturally appear in the HelloWork / Indeed corpora live here so any
regression is caught at the unit layer before the integration tests notice.
"""

from __future__ import annotations

from studentflow.models import ContractType
from studentflow.scrapers._text import (
    CONTRACT_PATTERNS,
    extract_city_from_dashed_title,
    guess_contract,
    strip_html,
)


def test_guess_contract_recognises_every_canonical_keyword() -> None:
    assert guess_contract("stage en entreprise") == ContractType.INTERNSHIP
    assert guess_contract("recherche stagiaire R&D") == ContractType.INTERNSHIP
    assert guess_contract("contrat en alternance") == ContractType.APPRENTICESHIP
    assert guess_contract("apprentissage 24 mois") == ContractType.APPRENTICESHIP
    assert guess_contract("apprenti boulanger") == ContractType.APPRENTICESHIP
    assert guess_contract("poste en CDI") == ContractType.CDI
    assert guess_contract("CDD de 6 mois") == ContractType.CDD
    assert guess_contract("temps partiel le week-end") == ContractType.PART_TIME
    assert guess_contract("part-time job") == ContractType.PART_TIME
    assert guess_contract("part time") == ContractType.PART_TIME
    assert guess_contract("Job étudiant") == ContractType.PART_TIME
    assert guess_contract("mission freelance") == ContractType.FREELANCE
    assert guess_contract("travailleur indépendant") == ContractType.FREELANCE
    assert guess_contract("travailleur independant") == ContractType.FREELANCE


def test_guess_contract_is_case_insensitive() -> None:
    assert guess_contract("STAGE 6 MOIS") == ContractType.INTERNSHIP
    assert guess_contract("Cdi temps plein") == ContractType.CDI


def test_guess_contract_returns_other_when_no_keyword_matches() -> None:
    assert guess_contract("") == ContractType.OTHER
    assert guess_contract("opportunité passionnante chez nous") == ContractType.OTHER
    # Embedded substring without word-boundary must NOT trigger a match.
    assert guess_contract("encadrement") == ContractType.OTHER  # contains "cadre" not "cdi"


def test_guess_contract_specific_keywords_win_over_generic() -> None:
    # "CDI en stage" — the more specific "stage" keyword should win because it
    # comes first in CONTRACT_PATTERNS. This protects against future reordering
    # accidentally degrading INTERNSHIP detection.
    assert guess_contract("Stage rémunéré convertible en CDI") == ContractType.INTERNSHIP


def test_contract_patterns_order_is_intentional() -> None:
    # Defensive: if someone reshuffles CONTRACT_PATTERNS, this test fails and
    # forces them to think about specificity ordering.
    types_in_order = [c for _, c in CONTRACT_PATTERNS]
    assert types_in_order.index(ContractType.INTERNSHIP) < types_in_order.index(ContractType.CDI)
    assert types_in_order.index(ContractType.APPRENTICESHIP) < types_in_order.index(
        ContractType.CDI
    )


def test_extract_city_from_dashed_title_trims_two_and_three_digit_dept_codes() -> None:
    assert extract_city_from_dashed_title("Job - Stage - Paris (75)") == "Paris"
    assert extract_city_from_dashed_title("Job - Stage - Bastia (2B)") == "Bastia (2B)"
    # Three-digit overseas codes (971, 972…) are stripped — they ARE digits.
    assert extract_city_from_dashed_title("Job - Stage - Saint-Denis (974)") == "Saint-Denis"


def test_extract_city_from_dashed_title_handles_missing_separator() -> None:
    assert extract_city_from_dashed_title("Single segment") == ""
    assert extract_city_from_dashed_title("") == ""


def test_extract_city_from_dashed_title_strips_whitespace() -> None:
    assert extract_city_from_dashed_title("Job -  Lyon  ") == "Lyon"
    assert extract_city_from_dashed_title("Job - Stage -   Marseille (13)  ") == "Marseille"


def test_strip_html_removes_tags_and_attributes() -> None:
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert strip_html('<a href="x">link</a>') == "link"
    assert strip_html("<br/>") == ""


def test_strip_html_returns_empty_for_empty_input() -> None:
    assert strip_html("") == ""


def test_strip_html_trims_outer_whitespace() -> None:
    assert strip_html("  <p>foo</p>  ") == "foo"
