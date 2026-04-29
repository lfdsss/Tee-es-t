"""Reusable test fixtures for StudentFlow."""

from __future__ import annotations

from datetime import date

from studentflow.models import ContractType, Offer, Source, Student


def make_offer(**overrides: object) -> Offer:
    base: dict[str, object] = {
        "source": Source.FRANCE_TRAVAIL,
        "source_id": "ft-001",
        "title": "Développeur React junior",
        "description": "Mission en alternance à Paris",
        "company": "Acme",
        "city": "Paris",
        "remote": False,
        "contract": ContractType.APPRENTICESHIP,
        "hours_per_week": 35,
        "skills": ["React", "JavaScript", "CSS"],
        "starts_on": date(2026, 9, 1),
        "ends_on": date(2027, 8, 31),
        "url": "https://example.com/offer/1",
    }
    base.update(overrides)
    return Offer(**base)  # type: ignore[arg-type]


def make_student(**overrides: object) -> Student:
    base: dict[str, object] = {
        "email": "emma@example.com",
        "full_name": "Emma Student",
        "city": "Paris",
        "remote_ok": True,
        "skills": ["React", "JavaScript", "TypeScript"],
        "accepted_contracts": [ContractType.APPRENTICESHIP, ContractType.INTERNSHIP],
        "max_hours_per_week": 40,
        "available_from": date(2026, 9, 1),
        "available_until": date(2027, 9, 1),
    }
    base.update(overrides)
    return Student(**base)  # type: ignore[arg-type]
