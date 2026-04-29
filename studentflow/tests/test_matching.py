"""Tests for the pure matching engine."""

from __future__ import annotations

from datetime import date

import pytest

from studentflow.matching import (
    WEIGHTS,
    _score_availability,
    _score_contract,
    _score_hours,
    _score_location,
    _score_skills,
    rank_offers_for_student,
    rank_students_for_offer,
    score,
)
from studentflow.models import ContractType

from .fixtures import make_offer, make_student


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_perfect_match_scores_near_one() -> None:
    shared_skills = ["React", "JavaScript", "CSS"]
    offer = make_offer(skills=shared_skills)
    student = make_student(skills=shared_skills)
    result = score(offer, student)
    assert result.score >= 0.99  # should be exactly 1.0 modulo rounding
    assert result.components["skills"] == 1.0
    assert result.components["location"] == 1.0


def test_mismatched_city_penalizes_location() -> None:
    offer = make_offer(city="Lyon", remote=False)
    student = make_student(city="Paris", remote_ok=False)
    s, reason, dist = _score_location(offer, student)
    assert "différentes" in reason.lower()
    assert s == 0.0
    assert dist is None


def test_remote_rescue_when_student_remote_ok() -> None:
    offer = make_offer(city="Lyon", remote=True)
    student = make_student(city="Paris", remote_ok=True)
    s, reason, _ = _score_location(offer, student)
    assert s == 1.0
    assert "remote" in reason.lower()


def test_location_uses_haversine_when_both_have_coords() -> None:
    """Paris (48.85, 2.35) ↔ Versailles (48.80, 2.13) ≈ 17 km → perfect score."""
    offer = make_offer(city="versailles", remote=False, latitude=48.8014, longitude=2.1301)
    student = make_student(city="paris", remote_ok=False, latitude=48.8566, longitude=2.3522)
    s, reason, dist = _score_location(offer, student)
    assert s == 1.0  # under 30 km soft threshold → perfect
    assert dist is not None and 10 < dist < 30
    assert "km" in reason


def test_location_haversine_penalises_far_distance() -> None:
    """Paris → Marseille ≈ 660 km → score 0 (hard cut at 80 km)."""
    offer = make_offer(city="marseille", remote=False, latitude=43.2965, longitude=5.3698)
    student = make_student(city="paris", remote_ok=False, latitude=48.8566, longitude=2.3522)
    s, _, dist = _score_location(offer, student)
    assert s == 0.0
    assert dist is not None and dist > 600


def test_skills_jaccard() -> None:
    offer = make_offer(skills=["React", "Python"])
    student = make_student(skills=["React", "Django"])
    s, _ = _score_skills(offer, student)
    # inter = {react} (1), union = {react, python, django} (3)
    assert s == pytest.approx(1 / 3, rel=1e-3)


def test_skills_no_overlap() -> None:
    offer = make_offer(skills=["Rust", "Go"])
    student = make_student(skills=["React", "TypeScript"])
    s, _ = _score_skills(offer, student)
    assert s == 0.0


def test_contract_accepted() -> None:
    offer = make_offer(contract=ContractType.APPRENTICESHIP)
    student = make_student(accepted_contracts=[ContractType.APPRENTICESHIP])
    s, _ = _score_contract(offer, student)
    assert s == 1.0


def test_contract_rejected() -> None:
    offer = make_offer(contract=ContractType.CDI)
    student = make_student(accepted_contracts=[ContractType.INTERNSHIP])
    s, _ = _score_contract(offer, student)
    assert s == 0.0


def test_hours_within_limit() -> None:
    offer = make_offer(hours_per_week=20)
    student = make_student(max_hours_per_week=35)
    s, _ = _score_hours(offer, student)
    assert s == 1.0


def test_hours_overflow_graceful() -> None:
    offer = make_offer(hours_per_week=40)
    student = make_student(max_hours_per_week=35)
    s, _ = _score_hours(offer, student)
    assert 0.0 < s < 1.0  # degrades, doesn't hit 0 immediately


def test_availability_compatible() -> None:
    offer = make_offer(starts_on=date(2026, 9, 1), ends_on=date(2027, 8, 31))
    student = make_student(available_from=date(2026, 9, 1), available_until=date(2027, 12, 31))
    s, _ = _score_availability(offer, student)
    assert s == 1.0


def test_availability_incompatible() -> None:
    offer = make_offer(starts_on=date(2027, 1, 1), ends_on=date(2027, 6, 30))
    student = make_student(available_from=date(2026, 1, 1), available_until=date(2026, 12, 31))
    s, _ = _score_availability(offer, student)
    assert s == 0.0


def test_rank_offers_for_student_sorts_desc() -> None:
    strong = make_offer(source_id="strong", title="Strong match")
    weak = make_offer(
        source_id="weak",
        title="Weak match",
        city="Lille",
        skills=["Rust"],
        contract=ContractType.CDI,
    )
    student = make_student()
    ranked = rank_offers_for_student([weak, strong], student, threshold=0.0)
    assert [o.title for o, _ in ranked] == ["Strong match", "Weak match"]


def test_rank_students_for_offer_skips_inactive() -> None:
    offer = make_offer()
    active = make_student()
    inactive = make_student(email="z@z.fr", active=False)
    ranked = rank_students_for_offer(offer, [active, inactive], threshold=0.0)
    emails = [s.email for s, _ in ranked]
    assert active.email in emails
    assert inactive.email not in emails


def test_score_components_align_with_weights() -> None:
    offer = make_offer()
    student = make_student()
    result = score(offer, student)
    reconstructed = sum(result.components[k] * WEIGHTS[k] for k in WEIGHTS)
    assert result.score == pytest.approx(round(reconstructed, 4), abs=1e-4)


def test_real_world_scenario_lucas_marketing_lyon() -> None:
    """Lucas: marketing student in Lyon, wants alternance."""
    offer = make_offer(
        source_id="ft-mkt",
        title="Alternance marketing digital",
        city="Lyon",
        contract=ContractType.APPRENTICESHIP,
        skills=["marketing", "seo", "community management"],
        hours_per_week=35,
    )
    lucas = make_student(
        email="lucas@example.com",
        city="Lyon",
        skills=["marketing", "seo", "réseaux sociaux"],
        accepted_contracts=[ContractType.APPRENTICESHIP],
        max_hours_per_week=35,
    )
    result = score(offer, lucas)
    assert result.score >= 0.8


def test_real_world_scenario_sarah_vente_toulouse() -> None:
    """Sarah: wants part-time sales job in Toulouse."""
    offer = make_offer(
        source_id="ft-sales",
        title="Vendeur week-end",
        city="Toulouse",
        contract=ContractType.PART_TIME,
        skills=["vente", "accueil client"],
        hours_per_week=12,
    )
    sarah = make_student(
        email="sarah@example.com",
        city="Toulouse",
        skills=["vente", "accueil client"],
        accepted_contracts=[ContractType.PART_TIME, ContractType.CDD],
        max_hours_per_week=15,
        remote_ok=False,
    )
    result = score(offer, sarah)
    assert result.score >= 0.95
