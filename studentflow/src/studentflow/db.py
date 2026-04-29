"""Repository layer on top of Supabase.

The concrete Supabase client is only imported when actually needed so that
tests and local development can run without the package installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from .config import Settings, get_settings
from .models import Match, Offer, Student

if TYPE_CHECKING:
    from supabase import Client


class Repository(Protocol):
    def upsert_offers(self, offers: list[Offer]) -> int: ...
    def list_active_students(self) -> list[Student]: ...
    def list_recent_unmatched_offers(self, limit: int = 200) -> list[Offer]: ...
    def insert_student(self, student: Student) -> None: ...
    def insert_match(self, match: Match) -> None: ...
    def list_unnotified_matches(self, limit: int = 100) -> list[Match]: ...
    def mark_match_notified(self, match_id: UUID) -> None: ...
    def get_offer(self, offer_id: UUID) -> Offer | None: ...
    def get_student(self, student_id: UUID) -> Student | None: ...
    def get_match_by_token(self, token: str) -> Match | None: ...
    def list_matches_for_student(self, student_id: UUID) -> list[Match]: ...
    def mark_match_accepted(self, match_id: UUID) -> None: ...
    def mark_match_declined(self, match_id: UUID) -> None: ...
    def count_offers(self) -> int: ...
    def count_students(self) -> int: ...
    def count_matches(self) -> int: ...
    def count_unnotified_matches(self) -> int: ...
    def count_matches_by_state(self) -> dict[str, int]: ...
    def count_offers_by_source(self) -> dict[str, int]: ...


class SupabaseRepository:
    """Thin wrapper around the Supabase Python client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            if not self._settings.supabase_configured:
                raise RuntimeError(
                    "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY."
                )
            from supabase import create_client

            self._client = create_client(
                self._settings.supabase_url,
                self._settings.supabase_service_key,
            )
        return self._client

    # ---- offers ----

    def upsert_offers(self, offers: list[Offer]) -> int:
        if not offers:
            return 0
        rows = [_offer_to_row(o) for o in offers]
        self.client.table("offers").upsert(rows, on_conflict="source,source_id").execute()
        return len(rows)

    def list_recent_unmatched_offers(self, limit: int = 200) -> list[Offer]:
        resp = (
            self.client.table("offers")
            .select("*")
            .order("scraped_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [_row_to_offer(r) for r in (resp.data or [])]

    # ---- students ----

    def list_active_students(self) -> list[Student]:
        resp = self.client.table("students").select("*").eq("active", True).execute()
        return [_row_to_student(r) for r in (resp.data or [])]

    def insert_student(self, student: Student) -> None:
        self.client.table("students").insert(_student_to_row(student)).execute()

    # ---- matches ----

    def insert_match(self, match: Match) -> None:
        self.client.table("matches").insert(_match_to_row(match)).execute()

    def list_unnotified_matches(self, limit: int = 100) -> list[Match]:
        resp = (
            self.client.table("matches").select("*").is_("notified_at", None).limit(limit).execute()
        )
        return [_row_to_match(r) for r in (resp.data or [])]

    def mark_match_notified(self, match_id: UUID) -> None:
        from datetime import datetime

        self.client.table("matches").update({"notified_at": datetime.utcnow().isoformat()}).eq(
            "id", str(match_id)
        ).execute()

    # ---- lookups (for notifier / API) ----

    def get_offer(self, offer_id: UUID) -> Offer | None:
        resp = self.client.table("offers").select("*").eq("id", str(offer_id)).limit(1).execute()
        rows = resp.data or []
        return _row_to_offer(rows[0]) if rows else None

    def get_student(self, student_id: UUID) -> Student | None:
        resp = (
            self.client.table("students").select("*").eq("id", str(student_id)).limit(1).execute()
        )
        rows = resp.data or []
        return _row_to_student(rows[0]) if rows else None

    def get_match_by_token(self, token: str) -> Match | None:
        resp = self.client.table("matches").select("*").eq("token", token).limit(1).execute()
        rows = resp.data or []
        return _row_to_match(rows[0]) if rows else None

    def list_matches_for_student(self, student_id: UUID) -> list[Match]:
        resp = (
            self.client.table("matches")
            .select("*")
            .eq("student_id", str(student_id))
            .order("created_at", desc=True)
            .execute()
        )
        return [_row_to_match(r) for r in (resp.data or [])]

    def mark_match_accepted(self, match_id: UUID) -> None:
        from datetime import datetime

        self.client.table("matches").update(
            {"state": "accepted", "accepted_at": datetime.utcnow().isoformat()}
        ).eq("id", str(match_id)).execute()

    def mark_match_declined(self, match_id: UUID) -> None:
        from datetime import datetime

        self.client.table("matches").update(
            {"state": "declined", "declined_at": datetime.utcnow().isoformat()}
        ).eq("id", str(match_id)).execute()

    # ---- stats ----

    def count_offers(self) -> int:
        resp = self.client.table("offers").select("id", count="exact").execute()
        return int(resp.count or 0)

    def count_students(self) -> int:
        resp = self.client.table("students").select("id", count="exact").execute()
        return int(resp.count or 0)

    def count_matches(self) -> int:
        resp = self.client.table("matches").select("id", count="exact").execute()
        return int(resp.count or 0)

    def count_unnotified_matches(self) -> int:
        resp = (
            self.client.table("matches")
            .select("id", count="exact")
            .is_("notified_at", None)
            .execute()
        )
        return int(resp.count or 0)

    def count_offers_by_source(self) -> dict[str, int]:
        resp = self.client.table("offers").select("source").execute()
        rows = resp.data or []
        out: dict[str, int] = {}
        for r in rows:
            src = r.get("source") or "unknown"
            out[src] = out.get(src, 0) + 1
        return out

    def count_matches_by_state(self) -> dict[str, int]:
        resp = self.client.table("matches").select("state").execute()
        rows = resp.data or []
        out: dict[str, int] = {}
        for r in rows:
            state = r.get("state") or "pending"
            out[state] = out.get(state, 0) + 1
        return out


# ---- row adapters ----
# These live at module level so they can be imported and tested standalone.


def _offer_to_row(o: Offer) -> dict[str, Any]:
    return {
        "id": str(o.id),
        "source": o.source.value,
        "source_id": o.source_id,
        "title": o.title,
        "description": o.description,
        "company": o.company,
        "city": o.city,
        "remote": o.remote,
        "contract": o.contract.value,
        "hours_per_week": o.hours_per_week,
        "skills": o.skills,
        "starts_on": o.starts_on.isoformat() if o.starts_on else None,
        "ends_on": o.ends_on.isoformat() if o.ends_on else None,
        "url": o.url,
        "contact_email": o.contact_email,
        "latitude": o.latitude,
        "longitude": o.longitude,
        "scraped_at": o.scraped_at.isoformat(),
    }


def _row_to_offer(row: dict[str, Any]) -> Offer:
    return Offer.model_validate(row)


def _student_to_row(s: Student) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "email": s.email,
        "full_name": s.full_name,
        "city": s.city,
        "remote_ok": s.remote_ok,
        "skills": s.skills,
        "accepted_contracts": [c.value for c in s.accepted_contracts],
        "max_hours_per_week": s.max_hours_per_week,
        "available_from": s.available_from.isoformat() if s.available_from else None,
        "available_until": s.available_until.isoformat() if s.available_until else None,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "active": s.active,
    }


def _row_to_student(row: dict[str, Any]) -> Student:
    return Student.model_validate(row)


def _match_to_row(m: Match) -> dict[str, Any]:
    return {
        "id": str(m.id),
        "offer_id": str(m.offer_id),
        "student_id": str(m.student_id),
        "score": m.score,
        "reasons": m.reasons,
        "token": m.token,
        "state": m.state.value,
        "distance_km": m.distance_km,
        "created_at": m.created_at.isoformat(),
        "notified_at": m.notified_at.isoformat() if m.notified_at else None,
        "accepted_at": m.accepted_at.isoformat() if m.accepted_at else None,
        "declined_at": m.declined_at.isoformat() if m.declined_at else None,
    }


def _row_to_match(row: dict[str, Any]) -> Match:
    return Match.model_validate(row)


class InMemoryRepository:
    """Repository used for local dev and tests. No external deps."""

    def __init__(self) -> None:
        self.offers: dict[tuple[str, str], Offer] = {}
        self.students: dict[UUID, Student] = {}
        self.matches: dict[UUID, Match] = {}

    def upsert_offers(self, offers: list[Offer]) -> int:
        for o in offers:
            self.offers[(o.source.value, o.source_id)] = o
        return len(offers)

    def list_active_students(self) -> list[Student]:
        return [s for s in self.students.values() if s.active]

    def list_recent_unmatched_offers(self, limit: int = 200) -> list[Offer]:
        return list(self.offers.values())[-limit:]

    def insert_student(self, student: Student) -> None:
        self.students[student.id] = student

    def insert_match(self, match: Match) -> None:
        self.matches[match.id] = match

    def list_unnotified_matches(self, limit: int = 100) -> list[Match]:
        return [m for m in self.matches.values() if m.notified_at is None][:limit]

    def mark_match_notified(self, match_id: UUID) -> None:
        from datetime import datetime

        m = self.matches.get(match_id)
        if m is not None:
            m.notified_at = datetime.utcnow()

    # ---- lookups ----

    def get_offer(self, offer_id: UUID) -> Offer | None:
        for offer in self.offers.values():
            if offer.id == offer_id:
                return offer
        return None

    def get_student(self, student_id: UUID) -> Student | None:
        return self.students.get(student_id)

    def get_match_by_token(self, token: str) -> Match | None:
        for m in self.matches.values():
            if m.token == token:
                return m
        return None

    def list_matches_for_student(self, student_id: UUID) -> list[Match]:
        found = [m for m in self.matches.values() if m.student_id == student_id]
        found.sort(key=lambda m: m.created_at, reverse=True)
        return found

    def mark_match_accepted(self, match_id: UUID) -> None:
        from datetime import datetime

        from .models import MatchState

        m = self.matches.get(match_id)
        if m is not None:
            m.state = MatchState.ACCEPTED
            m.accepted_at = datetime.utcnow()

    def mark_match_declined(self, match_id: UUID) -> None:
        from datetime import datetime

        from .models import MatchState

        m = self.matches.get(match_id)
        if m is not None:
            m.state = MatchState.DECLINED
            m.declined_at = datetime.utcnow()

    # ---- stats ----

    def count_offers(self) -> int:
        return len(self.offers)

    def count_students(self) -> int:
        return len(self.students)

    def count_matches(self) -> int:
        return len(self.matches)

    def count_unnotified_matches(self) -> int:
        return sum(1 for m in self.matches.values() if m.notified_at is None)

    def count_offers_by_source(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for offer in self.offers.values():
            src = offer.source.value
            out[src] = out.get(src, 0) + 1
        return out

    def count_matches_by_state(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for m in self.matches.values():
            key = m.state.value
            out[key] = out.get(key, 0) + 1
        return out
