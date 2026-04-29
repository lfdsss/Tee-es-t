"""Tests for the shared utils: geo maths + rule-based skill extraction."""

from __future__ import annotations

import pytest

from studentflow.utils.geo import distance_score, haversine_km
from studentflow.utils.skills import extract_skills, merge_skills


def test_haversine_zero_distance() -> None:
    assert haversine_km(48.85, 2.35, 48.85, 2.35) == pytest.approx(0.0, abs=1e-6)


def test_haversine_paris_marseille_known_distance() -> None:
    # Known great-circle distance: ~660 km.
    d = haversine_km(48.8566, 2.3522, 43.2965, 5.3698)
    assert 650 < d < 680


def test_haversine_paris_lyon_known_distance() -> None:
    d = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
    assert 380 < d < 410


def test_distance_score_curve() -> None:
    assert distance_score(10) == 1.0
    assert distance_score(30) == 1.0
    assert distance_score(80) == 0.0
    assert distance_score(150) == 0.0
    # Midpoint 55 km → score ~0.5
    mid = distance_score(55)
    assert 0.4 < mid < 0.6


def test_extract_skills_finds_tech_vocab() -> None:
    text = "On cherche un dev React / Node avec notions de SQL et Git. Bonus : Python."
    found = extract_skills(text)
    assert "react" in found
    assert "node" in found
    assert "sql" in found
    assert "git" in found
    assert "python" in found


def test_extract_skills_french_job_market_terms() -> None:
    text = (
        "Community manager pour notre boutique, gestion Canva, "
        "rédaction sur Instagram et TikTok. Anglais courant apprécié."
    )
    found = extract_skills(text)
    assert "community management" in found
    assert "canva" in found
    assert "social media" in found
    assert "rédaction" in found
    assert "anglais" in found


def test_extract_skills_is_case_insensitive() -> None:
    assert extract_skills("REACT Vue.js TypeScript") == extract_skills("react vue.js typescript")


def test_extract_skills_empty_text() -> None:
    assert extract_skills("") == []


def test_extract_skills_respects_word_boundaries() -> None:
    # "sql" shouldn't match inside "nosqlfoo" or "mysqlalt"
    assert "sql" not in extract_skills("nosqlfoo bar")


def test_merge_skills_dedupes_case_insensitive() -> None:
    merged = merge_skills(["React", "python"], ["react", "SQL"])
    assert merged == ["react", "python", "sql"]
