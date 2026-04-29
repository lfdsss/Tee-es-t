"""Pure matching engine. No I/O, no DB, no network.

Testable unit by unit. Every component returns a score in [0, 1] and a reason
string. `score()` is a weighted sum and returns a `MatchResult`.

If you add a new component, wire it in `WEIGHTS` and in `score()`, then add
tests in `tests/test_matching.py`.
"""

from __future__ import annotations

from datetime import date

from .models import ContractType, MatchResult, Offer, Student
from .utils.geo import distance_score, haversine_km

WEIGHTS: dict[str, float] = {
    "skills": 0.40,
    "location": 0.25,
    "contract": 0.15,
    "hours": 0.10,
    "availability": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must sum to 1.0"


def _score_skills(offer: Offer, student: Student) -> tuple[float, str]:
    """Jaccard overlap between offer and student skills."""
    off = set(offer.skills)
    stu = set(student.skills)
    if not off:
        return 0.5, "Offre sans skills listés (neutre)"
    if not stu:
        return 0.0, "Étudiant sans skills renseignés"
    inter = off & stu
    union = off | stu
    score = len(inter) / len(union) if union else 0.0
    if score == 1.0:
        return 1.0, f"Toutes les skills matchent ({len(inter)})"
    if score >= 0.5:
        return score, f"Skills partiellement alignées: {sorted(inter)}"
    if score > 0:
        return score, f"Skills peu alignées: {sorted(inter)}"
    return 0.0, "Aucune skill commune"


def _score_location(offer: Offer, student: Student) -> tuple[float, str, float | None]:
    """Location score + reason + optional distance in km.

    Priority order: remote match > Haversine distance (if both coords) > city
    string equality > fallback. Returning distance separately lets the API
    display "12 km de chez toi" without re-computing.
    """
    if offer.remote and student.remote_ok:
        return 1.0, "Offre remote, étudiant OK remote", None

    have_coords = (
        offer.latitude is not None
        and offer.longitude is not None
        and student.latitude is not None
        and student.longitude is not None
    )
    if have_coords:
        dist = haversine_km(
            offer.latitude,  # type: ignore[arg-type]
            offer.longitude,  # type: ignore[arg-type]
            student.latitude,  # type: ignore[arg-type]
            student.longitude,  # type: ignore[arg-type]
        )
        score = distance_score(dist)
        return score, f"{round(dist)} km de chez toi", round(dist, 1)

    if not offer.city and not student.city:
        return 0.5, "Aucune ville renseignée", None
    if offer.city and student.city and offer.city == student.city:
        return 1.0, f"Même ville ({offer.city})", 0.0
    if offer.remote:
        return 0.3, "Offre remote mais étudiant préfère présentiel", None
    return 0.0, f"Villes différentes ({offer.city} vs {student.city})", None


def _score_contract(offer: Offer, student: Student) -> tuple[float, str]:
    if not student.accepted_contracts:
        return 0.5, "Étudiant n'a pas précisé ses contrats"
    if offer.contract in student.accepted_contracts:
        return 1.0, f"Contrat accepté ({offer.contract.value})"
    if offer.contract == ContractType.OTHER:
        return 0.5, "Contrat offre non spécifié"
    return 0.0, f"Contrat {offer.contract.value} non accepté"


def _score_hours(offer: Offer, student: Student) -> tuple[float, str]:
    if offer.hours_per_week is None:
        return 0.5, "Heures/sem non précisées"
    if offer.hours_per_week <= student.max_hours_per_week:
        return 1.0, f"{offer.hours_per_week}h/sem ≤ {student.max_hours_per_week}h max"
    overflow = offer.hours_per_week - student.max_hours_per_week
    # Gradual penalty: -5% per extra hour.
    score = max(0.0, 1.0 - overflow * 0.05)
    return score, f"{offer.hours_per_week}h/sem > {student.max_hours_per_week}h max"


def _score_availability(offer: Offer, student: Student) -> tuple[float, str]:
    """Rough overlap check between offer window and student window."""
    # If nothing specified, stay neutral.
    if not offer.starts_on and not student.available_from:
        return 0.5, "Disponibilités non précisées"

    offer_start = offer.starts_on or date.min
    offer_end = offer.ends_on or date.max
    stu_start = student.available_from or date.min
    stu_end = student.available_until or date.max

    overlap_start = max(offer_start, stu_start)
    overlap_end = min(offer_end, stu_end)

    if overlap_start > overlap_end:
        return 0.0, "Fenêtres de disponibilité incompatibles"
    return 1.0, "Disponibilités compatibles"


def score(offer: Offer, student: Student) -> MatchResult:
    """Compute the overall match score between an offer and a student.

    Returns a `MatchResult` with:
      - score ∈ [0, 1] (weighted sum of components)
      - reasons: human-readable explanation per component
      - components: raw component scores by name
    """
    components: dict[str, float] = {}
    reasons: list[str] = []

    s_skills, r_skills = _score_skills(offer, student)
    components["skills"] = s_skills
    reasons.append(f"[skills {s_skills:.2f}] {r_skills}")

    s_loc, r_loc, distance_km = _score_location(offer, student)
    components["location"] = s_loc
    reasons.append(f"[location {s_loc:.2f}] {r_loc}")

    s_contract, r_contract = _score_contract(offer, student)
    components["contract"] = s_contract
    reasons.append(f"[contract {s_contract:.2f}] {r_contract}")

    s_hours, r_hours = _score_hours(offer, student)
    components["hours"] = s_hours
    reasons.append(f"[hours {s_hours:.2f}] {r_hours}")

    s_avail, r_avail = _score_availability(offer, student)
    components["availability"] = s_avail
    reasons.append(f"[availability {s_avail:.2f}] {r_avail}")

    total = sum(components[name] * WEIGHTS[name] for name in WEIGHTS)
    return MatchResult(
        score=round(total, 4),
        reasons=reasons,
        components=components,
        distance_km=distance_km,
    )


def rank_offers_for_student(
    offers: list[Offer], student: Student, threshold: float = 0.6
) -> list[tuple[Offer, MatchResult]]:
    """Return offers scored >= threshold, sorted desc by score."""
    scored = [(o, score(o, student)) for o in offers]
    kept = [(o, m) for o, m in scored if m.score >= threshold]
    kept.sort(key=lambda pair: pair[1].score, reverse=True)
    return kept


def rank_students_for_offer(
    offer: Offer, students: list[Student], threshold: float = 0.6
) -> list[tuple[Student, MatchResult]]:
    """Return students scored >= threshold, sorted desc by score."""
    scored = [(s, score(offer, s)) for s in students if s.active]
    kept = [(s, m) for s, m in scored if m.score >= threshold]
    kept.sort(key=lambda pair: pair[1].score, reverse=True)
    return kept
