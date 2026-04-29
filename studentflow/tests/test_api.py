"""Integration tests for the FastAPI app.

We bypass the cached repository singleton by instantiating `InMemoryRepository`
per test and overriding the dependency. This mirrors production wiring
(Repository protocol) without any external service.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from studentflow.api import app, get_repository
from studentflow.db import InMemoryRepository
from studentflow.models import MatchState

from .fixtures import make_offer, make_student


@pytest.fixture
def repo() -> InMemoryRepository:
    return InMemoryRepository()


@pytest.fixture
def client(repo: InMemoryRepository) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_student_returns_cold_start_matches(
    client: TestClient, repo: InMemoryRepository
) -> None:
    """Signup should already surface strong-matching offers in the response."""
    repo.upsert_offers(
        [
            make_offer(
                source_id="cold-1",
                title="Alternance React Paris",
                skills=["React", "TypeScript", "CSS"],
            )
        ]
    )

    resp = client.post(
        "/students",
        json={
            "email": "cold@example.com",
            "full_name": "Cold Start",
            "city": "Paris",
            "remote_ok": True,
            "skills": ["react", "typescript", "css"],
            "accepted_contracts": ["apprenticeship", "internship"],
            "max_hours_per_week": 35,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["completeness"] >= 0.6
    assert len(body["matches"]) == 1
    assert body["matches"][0]["title"].startswith("Alternance")
    # One Match row persisted so the inbox keeps it on refresh.
    assert len(repo.matches) == 1


def test_create_student_no_matches_when_offers_empty(client: TestClient) -> None:
    resp = client.post(
        "/students",
        json={
            "email": "solo@example.com",
            "full_name": "Solo",
            "city": "Paris",
            "remote_ok": True,
            "skills": ["react"],
            "accepted_contracts": ["internship"],
            "max_hours_per_week": 20,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["matches"] == []


def test_create_offer_auto_extracts_skills_from_description(
    client: TestClient, repo: InMemoryRepository
) -> None:
    resp = client.post(
        "/offers",
        json={
            "title": "Community manager",
            "company": "La Française des Sauces",
            "description": (
                "Animation Instagram + TikTok, rédaction de posts, "
                "utilisation de Canva. Anglais courant."
            ),
            "city": "Paris",
            "remote": False,
            "contract": "part_time",
            "hours_per_week": 10,
            "skills": [],  # employer left it blank → we auto-enrich
            "url": "",
            "contact_email": "hr@lfds.fr",
        },
    )
    assert resp.status_code == 201
    assert len(repo.offers) == 1
    offer = next(iter(repo.offers.values()))
    assert "community management" in offer.skills
    assert "canva" in offer.skills
    assert "social media" in offer.skills


def test_accept_match_flow_marks_accepted(client: TestClient, repo: InMemoryRepository) -> None:
    """One-click accept → state transitions, idempotent on replay."""
    from studentflow.agents import MatcherAgent

    offer = make_offer(
        contact_email="hr@acme.fr",
        # manual submission mimic so the employer relay path has an email
    )
    repo.upsert_offers([offer])
    repo.insert_student(make_student())
    # Run the matcher once so a Match row exists.
    import asyncio

    asyncio.run(MatcherAgent(repo, threshold=0.6).tick())
    match = next(iter(repo.matches.values()))
    assert match.state == MatchState.PENDING

    r1 = client.get(f"/m/{match.token}/accept")
    assert r1.status_code == 200
    assert "accepté" in r1.text.lower()
    assert repo.matches[match.id].state == MatchState.ACCEPTED

    # Idempotent: second call returns 200 with "déjà accepté".
    r2 = client.get(f"/m/{match.token}/accept")
    assert r2.status_code == 200
    assert "déjà" in r2.text.lower()


def test_decline_match_flow(client: TestClient, repo: InMemoryRepository) -> None:
    import asyncio

    from studentflow.agents import MatcherAgent

    repo.upsert_offers([make_offer()])
    repo.insert_student(make_student())
    asyncio.run(MatcherAgent(repo, threshold=0.6).tick())
    match = next(iter(repo.matches.values()))

    resp = client.get(f"/m/{match.token}/decline")
    assert resp.status_code == 200
    assert repo.matches[match.id].state == MatchState.DECLINED


def test_accept_unknown_token_returns_404(client: TestClient) -> None:
    resp = client.get("/m/nope-nope-nope/accept")
    assert resp.status_code == 404


def test_list_student_matches_hides_declined(client: TestClient, repo: InMemoryRepository) -> None:
    import asyncio

    from studentflow.agents import MatcherAgent

    repo.upsert_offers([make_offer()])
    student = make_student()
    repo.insert_student(student)
    asyncio.run(MatcherAgent(repo, threshold=0.6).tick())
    match = next(iter(repo.matches.values()))

    r1 = client.get(f"/students/{student.id}/matches")
    assert r1.status_code == 200
    assert len(r1.json()) == 1

    repo.mark_match_declined(match.id)
    r2 = client.get(f"/students/{student.id}/matches")
    assert r2.json() == []


def test_create_offer_returns_candidates_inline(
    client: TestClient, repo: InMemoryRepository
) -> None:
    """Employer-side cold-start: POST /offers returns top students inline."""
    repo.insert_student(
        make_student(
            email="alice@ex.com",
            skills=["community management", "canva", "social media"],
        )
    )
    repo.insert_student(make_student(email="bob@ex.com", skills=["python", "sql"]))

    resp = client.post(
        "/offers",
        json={
            "title": "Community manager",
            "company": "LFDS",
            "description": "Animation Instagram, Canva, rédaction.",
            "city": "Paris",
            "remote": True,
            "contract": "part_time",
            "hours_per_week": 10,
            "skills": [],
            "url": "",
            "contact_email": "hr@lfds.fr",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert len(body["enriched_skills"]) > 0
    # Alice's skills match; Bob's don't.
    emails = [c["email"] for c in body["candidates"]]
    assert "alice@ex.com" in emails


def test_funnel_endpoint_reports_acceptance_rate(
    client: TestClient, repo: InMemoryRepository
) -> None:
    import asyncio

    from studentflow.agents import MatcherAgent

    repo.upsert_offers([make_offer(source_id=f"off-{i}") for i in range(3)])
    repo.insert_student(make_student())
    asyncio.run(MatcherAgent(repo, threshold=0.6).tick())
    ms = list(repo.matches.values())
    repo.mark_match_accepted(ms[0].id)
    repo.mark_match_declined(ms[1].id)

    body = client.get("/stats/funnel").json()
    assert body["matches"]["total"] == 3
    assert body["matches"]["accepted"] == 1
    assert body["matches"]["declined"] == 1
    assert body["matches"]["pending"] == 1
    assert body["acceptance_rate"] == 0.5  # 1 / (1 + 1)
    assert body["decision_rate"] == round(2 / 3, 3)


def test_skill_vocabulary_is_exposed(client: TestClient) -> None:
    body = client.get("/skills/vocabulary").json()
    assert "python" in body["skills"]
    assert "community management" in body["skills"]


def test_skill_extract_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/skills/extract",
        json={"text": "Stage en développement web React avec TypeScript. Anglais courant."},
    )
    assert resp.status_code == 200
    skills = resp.json()["skills"]
    assert "react" in skills
    assert "typescript" in skills
    assert "anglais" in skills
