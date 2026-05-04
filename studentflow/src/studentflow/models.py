"""Pydantic domain models.

These models are the ground truth for every boundary of the system: scrapers
return them, the matching engine consumes them, the API serializes them, and
the DB layer persists them. Keep them dumb — no I/O, no business rules beyond
validation.
"""

from __future__ import annotations

import secrets
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ContractType(StrEnum):
    INTERNSHIP = "internship"  # stage
    APPRENTICESHIP = "apprenticeship"  # alternance
    CDD = "cdd"
    CDI = "cdi"
    PART_TIME = "part_time"  # job étudiant
    FREELANCE = "freelance"
    OTHER = "other"


class Source(StrEnum):
    FRANCE_TRAVAIL = "france_travail"
    INDEED = "indeed"
    HELLOWORK = "hellowork"
    STUDENTJOB = "studentjob"
    JOBTEASER = "jobteaser"
    ADZUNA = "adzuna"
    JOOBLE = "jooble"


class MatchState(StrEnum):
    """Lifecycle of a match from the student's perspective.

    PENDING  — notified, awaiting the student's decision.
    ACCEPTED — student clicked accept; employer relay should fire.
    DECLINED — student passed; match stays in history but stops showing.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


def _norm_skills(skills: list[str]) -> list[str]:
    """Lowercase + strip + dedupe while preserving insertion order."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in skills:
        s = raw.strip().lower()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _new_match_token() -> str:
    """URL-safe opaque token used to accept/decline a match in one click."""
    return secrets.token_urlsafe(24)


class Offer(BaseModel):
    model_config = ConfigDict(frozen=False)

    id: UUID = Field(default_factory=uuid4)
    source: Source
    source_id: str  # unique within (source, source_id)
    title: str
    description: str = ""
    company: str = ""
    city: str = ""
    remote: bool = False
    contract: ContractType = ContractType.OTHER
    hours_per_week: int | None = None
    skills: list[str] = Field(default_factory=list)
    starts_on: date | None = None
    ends_on: date | None = None
    url: str = ""
    contact_email: str = ""  # set when an employer publishes via POST /offers
    latitude: float | None = None
    longitude: float | None = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, _: object) -> None:
        object.__setattr__(self, "skills", _norm_skills(self.skills))
        object.__setattr__(self, "city", self.city.strip().lower())


class Student(BaseModel):
    model_config = ConfigDict(frozen=False)

    id: UUID = Field(default_factory=uuid4)
    email: str
    full_name: str = ""
    city: str = ""
    remote_ok: bool = True
    skills: list[str] = Field(default_factory=list)
    accepted_contracts: list[ContractType] = Field(default_factory=list)
    max_hours_per_week: int = 20
    available_from: date | None = None
    available_until: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    active: bool = True

    def model_post_init(self, _: object) -> None:
        object.__setattr__(self, "skills", _norm_skills(self.skills))
        object.__setattr__(self, "city", self.city.strip().lower())

    @property
    def completeness(self) -> float:
        """0-1 heuristic on how many profile slots the student filled.

        Drives a progress bar in the UI and influences how aggressively we
        recommend the profile to employers (more info = better ranking).
        """
        signals = [
            bool(self.full_name),
            bool(self.city) or (self.latitude is not None and self.longitude is not None),
            len(self.skills) >= 3,
            bool(self.accepted_contracts),
            self.available_from is not None,
        ]
        return round(sum(1 for s in signals if s) / len(signals), 2)


class MatchResult(BaseModel):
    """Output of the matching engine. Not persisted as-is."""

    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    components: dict[str, float] = Field(default_factory=dict)
    distance_km: float | None = None


class Match(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    offer_id: UUID
    student_id: UUID
    score: float
    reasons: list[str] = Field(default_factory=list)
    token: str = Field(default_factory=_new_match_token)
    state: MatchState = MatchState.PENDING
    distance_km: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notified_at: datetime | None = None
    accepted_at: datetime | None = None
    declined_at: datetime | None = None


class Notification(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    channel: str = "webhook"
    payload: dict[str, object] = Field(default_factory=dict)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    succeeded: bool = True
    error: str | None = None
