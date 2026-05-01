"""Shared text helpers for scrapers.

Multiple scrapers (HelloWork RSS, Indeed RSS, and any future HTML-based source
like studentjob.fr) face the same three problems on every offer:

  1. Guess the French contract type (CDI / CDD / stage / alternance / etc.)
     from a free-text blob — title + description.
  2. Extract a city out of the kind of dashed title boards typically emit
     (`Job title - Company - City (dept)`).
  3. Strip HTML tags out of a description without pulling in BeautifulSoup
     when ElementTree already gives us the raw text.

Each scraper used to carry its own copy of these. That made adding a new
scraper a copy-paste job and meant any vocabulary fix had to be applied N
times. This module is the single source of truth — every concrete scraper
imports from here.

Pure functions, zero I/O, zero state. Safe to call inline in hot paths.
"""

from __future__ import annotations

import re

from ..models import ContractType

CONTRACT_PATTERNS: list[tuple[re.Pattern[str], ContractType]] = [
    (re.compile(r"\b(stage|stagiaire)\b", re.I), ContractType.INTERNSHIP),
    (re.compile(r"\b(alternance|apprentissage|apprenti)\b", re.I), ContractType.APPRENTICESHIP),
    (re.compile(r"\bcdi\b", re.I), ContractType.CDI),
    (re.compile(r"\bcdd\b", re.I), ContractType.CDD),
    (
        re.compile(r"\b(temps partiel|part.?time|week.?end|job étudiant)\b", re.I),
        ContractType.PART_TIME,
    ),
    (re.compile(r"\b(freelance|indépendant|independant)\b", re.I), ContractType.FREELANCE),
]

_HTML_TAG = re.compile(r"<[^>]+>")
_DEPT_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


def guess_contract(text: str) -> ContractType:
    """Return the first matching `ContractType` for `text`, else `OTHER`.

    Patterns are evaluated in declaration order, so the most specific keywords
    (stage, alternance) win over generic ones (CDI/CDD).
    """
    for pattern, contract in CONTRACT_PATTERNS:
        if pattern.search(text):
            return contract
    return ContractType.OTHER


def extract_city_from_dashed_title(title: str) -> str:
    """Pull the city out of a title shaped like `Foo - Bar - City (75)`.

    Returns the last ` - `-separated segment with any trailing department code
    stripped. Falls back to empty string when the title has no dash separator.
    """
    parts = [p.strip() for p in title.split(" - ")]
    if len(parts) < 2:
        return ""
    return _DEPT_SUFFIX.sub("", parts[-1])


def strip_html(raw: str) -> str:
    """Remove all HTML tags from `raw`. Cheap, regex-based, good for snippets."""
    return _HTML_TAG.sub("", raw).strip()
