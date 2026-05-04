"""Sanity tests for the Pydantic models."""

from __future__ import annotations

from studentflow.models import ContractType, Offer, Source, Student


def test_offer_normalizes_skills_and_city() -> None:
    offer = Offer(
        source=Source.FRANCE_TRAVAIL,
        source_id="x1",
        title="t",
        skills=["  React  ", "react", "JavaScript"],
        city="  Paris  ",
    )
    assert offer.skills == ["react", "javascript"]
    assert offer.city == "paris"


def test_student_normalizes_skills_and_city() -> None:
    student = Student(
        email="a@b.fr",
        skills=["Python", "python", "SQL"],
        city="LYON",
    )
    assert student.skills == ["python", "sql"]
    assert student.city == "lyon"


def test_contract_type_enum() -> None:
    assert ContractType("internship") is ContractType.INTERNSHIP
