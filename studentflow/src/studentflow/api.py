"""FastAPI application.

Public surface of StudentFlow. Thin on purpose — the real value lives in the
matching engine and the agents. The API:

  * onboards students and scores them instantly against the active offer set
    (cold-start matches returned in the POST response, so they never land on
    an empty inbox),
  * lets employers publish missions and auto-enriches them with skills mined
    from the description (the matcher only works if offer.skills is rich),
  * lets a student accept or decline a match in one click via a signed token
    URL embedded in the notification email,
  * streams new matches live to the student's browser via SSE so the inbox
    refreshes without polling.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from .config import get_settings
from .db import InMemoryRepository, Repository, SupabaseRepository
from .matching import rank_offers_for_student, rank_students_for_offer
from .models import ContractType, Match, MatchState, Offer, Source, Student
from .realtime import broadcaster
from .utils.skills import VOCABULARY, extract_skills, merge_skills

log = logging.getLogger(__name__)

app = FastAPI(
    title="StudentFlow API",
    version="0.2.0",
    description="Real-time matching between student job offers and student profiles",
)

# CORS: the SPA lives on a different origin in prod (Netlify). Keep it open for
# the public endpoints — there's no auth yet, and all data is user-provided.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- repository dependency ----


_repo_cache: Repository | None = None


def get_repository() -> Repository:
    """Return a Supabase repo if configured, else an in-memory one.

    The in-memory fallback lets you run the API locally without any external
    service — perfect for development and tests.
    """
    global _repo_cache
    if _repo_cache is not None:
        return _repo_cache
    settings = get_settings()
    if settings.supabase_configured:
        _repo_cache = SupabaseRepository(settings)
    else:
        _repo_cache = InMemoryRepository()
    return _repo_cache


# ---- request / response models ----


class StudentCreate(BaseModel):
    email: EmailStr
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


class MatchOut(BaseModel):
    offer_id: UUID
    match_id: UUID | None = None
    title: str
    company: str
    city: str
    url: str = ""
    score: float
    reasons: list[str]
    distance_km: float | None = None
    state: MatchState = MatchState.PENDING


class OfferCreate(BaseModel):
    """Body used when an employer publishes a mission through the web app."""

    title: str
    company: str
    description: str = ""
    city: str = ""
    remote: bool = False
    contract: ContractType = ContractType.PART_TIME
    hours_per_week: int | None = None
    skills: list[str] = Field(default_factory=list)
    url: str = ""
    contact_email: EmailStr | None = None
    latitude: float | None = None
    longitude: float | None = None


class StudentMatchOut(BaseModel):
    student_id: UUID
    full_name: str
    email: str
    city: str
    skills: list[str]
    score: float
    reasons: list[str]
    distance_km: float | None = None


class StudentCreateResponse(BaseModel):
    id: UUID
    completeness: float
    matches: list[MatchOut] = Field(default_factory=list)


class OfferCreateResponse(BaseModel):
    """Mirrors StudentCreateResponse on the employer side — never land on
    an empty candidate list. Employers get their top students inline."""

    id: UUID
    enriched_skills: list[str] = Field(default_factory=list)
    candidates: list[StudentMatchOut] = Field(default_factory=list)


class SkillExtractRequest(BaseModel):
    text: str


# ---- routes ----


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}


@app.post("/students", status_code=201, response_model=StudentCreateResponse)
def create_student(
    payload: StudentCreate, repo: Repository = Depends(get_repository)
) -> StudentCreateResponse:
    """Onboard a student AND return top matches immediately.

    Cold-start problem killer: new students land on `/matches/:id` with a
    non-empty inbox on the very first page load, so the perceived value is
    immediate instead of "come back in 15 min".
    """
    student = Student(**payload.model_dump())
    repo.insert_student(student)

    threshold = get_settings().match_score_threshold
    offers = repo.list_recent_unmatched_offers()
    ranked = rank_offers_for_student(offers, student, threshold=threshold)

    cold_matches: list[MatchOut] = []
    for offer, result in ranked[:10]:
        m = Match(
            offer_id=offer.id,
            student_id=student.id,
            score=result.score,
            reasons=result.reasons,
            distance_km=result.distance_km,
        )
        repo.insert_match(m)
        cold_matches.append(
            MatchOut(
                offer_id=offer.id,
                match_id=m.id,
                title=offer.title,
                company=offer.company,
                city=offer.city,
                url=offer.url,
                score=result.score,
                reasons=result.reasons,
                distance_km=result.distance_km,
                state=m.state,
            )
        )
        broadcaster.publish(student.id, {"type": "match", "match_id": str(m.id)})
        broadcaster.publish_offer(
            offer.id, {"type": "candidate", "match_id": str(m.id), "student_id": str(student.id)}
        )

    return StudentCreateResponse(
        id=student.id,
        completeness=student.completeness,
        matches=cold_matches,
    )


@app.get("/stats")
def stats(repo: Repository = Depends(get_repository)) -> dict[str, object]:
    """Lightweight aggregates for dashboards and ops health-checks."""
    return {
        "offers": repo.count_offers(),
        "students": repo.count_students(),
        "matches": repo.count_matches(),
        "matches_unnotified": repo.count_unnotified_matches(),
        "per_source": repo.count_offers_by_source(),
    }


@app.get("/stats/funnel")
def funnel(repo: Repository = Depends(get_repository)) -> dict[str, object]:
    """Full conversion funnel — offers → matches → accepts.

    Drives the admin dashboard and the homepage social-proof counter. The
    acceptance rate is the key engagement KPI: below 30% and notifications
    are too loose; above 70% and we're under-indexing candidates.
    """
    states = repo.count_matches_by_state()
    accepted = states.get("accepted", 0)
    declined = states.get("declined", 0)
    pending = states.get("pending", 0)
    total = accepted + declined + pending
    decided = accepted + declined
    return {
        "offers": repo.count_offers(),
        "students": repo.count_students(),
        "matches": {
            "total": total,
            "pending": pending,
            "accepted": accepted,
            "declined": declined,
        },
        "acceptance_rate": round(accepted / decided, 3) if decided else None,
        "decision_rate": round(decided / total, 3) if total else None,
        "per_source": repo.count_offers_by_source(),
    }


@app.get("/skills/vocabulary")
def skill_vocabulary() -> dict[str, list[str]]:
    """Canonical skill list the matcher understands.

    Powers the student signup autocomplete — typing "comm" suggests
    `community management`. Keeps the vocabulary students type aligned with
    what the matcher scores, so Jaccard stays honest.
    """
    return {"skills": VOCABULARY}


@app.post("/skills/extract")
def extract_skills_endpoint(payload: SkillExtractRequest) -> dict[str, list[str]]:
    """Deterministic CV/description → canonical skill list.

    Student pastes a CV or job description, we return the skills we
    recognised. Zero LLM, zero cost, fully deterministic. The student can
    then accept / edit the list before hitting submit.
    """
    return {"skills": extract_skills(payload.text)}


@app.get("/students/{student_id}/matches", response_model=list[MatchOut])
def list_matches_for_student(
    student_id: UUID, repo: Repository = Depends(get_repository)
) -> list[MatchOut]:
    """Return stored matches for this student, newest first.

    We serve the persisted Match rows so the UI can show pending/accepted/
    declined state and the exact stored distance. Scoring on the fly would
    lose that per-match lifecycle.
    """
    student = repo.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    stored = repo.list_matches_for_student(student_id)
    out: list[MatchOut] = []
    for match in stored:
        if match.state == MatchState.DECLINED:
            continue
        offer = repo.get_offer(match.offer_id)
        if offer is None:
            continue
        out.append(
            MatchOut(
                offer_id=offer.id,
                match_id=match.id,
                title=offer.title,
                company=offer.company,
                city=offer.city,
                url=offer.url,
                score=match.score,
                reasons=match.reasons,
                distance_km=match.distance_km,
                state=match.state,
            )
        )
    return out


@app.get("/students/{student_id}/stream")
async def stream_matches(
    student_id: UUID,
    request: Request,
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    """Server-Sent Events stream: live match events for this student.

    Browsers get an `EventSource` connection that emits `data: {...}` every
    time the MatcherAgent (or the cold-start path) publishes a new match.
    Disconnects and process restarts are absorbed: the client just reconnects
    and will see future events — past matches are available via the REST
    listing route.
    """
    if repo.get_student(student_id) is None:
        raise HTTPException(status_code=404, detail="Student not found")

    async def event_stream():
        yield b": stream open\n\n"
        async with broadcaster.subscribe(student_id) as queue:
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n".encode()
                except TimeoutError:
                    # Keep-alive ping to prevent intermediaries from closing.
                    yield b": keep-alive\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables buffering on nginx-style proxies
        },
    )


@app.get("/offers/{offer_id}/stream")
async def stream_candidates(
    offer_id: UUID,
    request: Request,
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    """SSE stream: live candidate events for an employer's offer.

    Mirror of the student stream. Every time the MatcherAgent creates a new
    match for this offer, the employer's browser receives a push event and
    auto-refreshes the candidate list — real Uber-grade live experience.
    """
    if repo.get_offer(offer_id) is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    async def event_stream():
        yield b": stream open\n\n"
        async with broadcaster.subscribe_offer(offer_id) as queue:
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n".encode()
                except TimeoutError:
                    yield b": keep-alive\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---- accept / decline one-click flow -----------------------------------


def _accept_html(title: str, body: str) -> str:
    # Self-contained so the student sees a friendly confirmation page even if
    # the SPA is down. Zero external assets.
    return f"""<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — StudentFlow</title>
<style>
body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:#0b0d10;color:#e6e9ef;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:1rem}}
.card{{max-width:480px;background:#12161c;border:1px solid #242a33;border-radius:14px;padding:2rem;text-align:center}}
h1{{margin:0 0 0.5rem 0;font-size:1.5rem}}
p{{color:#9aa4b2;line-height:1.6}}
.ok{{color:#31c48d}}.ko{{color:#f87171}}
</style>
</head><body><div class="card">{body}</div></body></html>"""


@app.get("/m/{token}/accept", response_class=HTMLResponse)
async def accept_match(token: str, repo: Repository = Depends(get_repository)) -> HTMLResponse:
    """One-click accept from the notification email.

    Idempotent: clicking twice doesn't re-notify the employer. On first accept
    we fire an async employer-relay webhook when the offer has a contact_email.
    """
    match = repo.get_match_by_token(token)
    if match is None:
        return HTMLResponse(
            _accept_html(
                "Lien invalide",
                "<h1 class='ko'>Lien invalide</h1><p>Ce match n'existe pas ou le lien a expiré.</p>",
            ),
            status_code=404,
        )

    if match.state == MatchState.ACCEPTED:
        return HTMLResponse(
            _accept_html(
                "Déjà accepté",
                "<h1 class='ok'>Déjà accepté ✓</h1><p>L'entreprise a été prévenue. Elle te contactera directement.</p>",
            )
        )

    repo.mark_match_accepted(match.id)
    student = repo.get_student(match.student_id)
    offer = repo.get_offer(match.offer_id)

    broadcaster.publish(
        match.student_id,
        {"type": "match_accepted", "match_id": str(match.id)},
    )
    broadcaster.publish_offer(
        match.offer_id,
        {
            "type": "candidate_accepted",
            "match_id": str(match.id),
            "student_id": str(match.student_id),
        },
    )

    # Fire-and-forget employer relay: we don't want the student's HTTP call
    # to wait on an SMTP handshake.
    if offer is not None and student is not None and offer.contact_email:
        asyncio.create_task(_relay_to_employer(match=match, student=student, offer=offer))

    title = offer.title if offer else "l'offre"
    company = offer.company if offer else "l'entreprise"
    return HTMLResponse(
        _accept_html(
            "Match accepté",
            f"<h1 class='ok'>C'est noté ✓</h1><p>Tu viens d'accepter <strong>{title}</strong> chez <strong>{company}</strong>. "
            f"On prévient l'entreprise immédiatement — elle te contactera par email.</p>",
        )
    )


@app.get("/m/{token}/decline", response_class=HTMLResponse)
async def decline_match(token: str, repo: Repository = Depends(get_repository)) -> HTMLResponse:
    """One-click pass."""
    match = repo.get_match_by_token(token)
    if match is None:
        return HTMLResponse(
            _accept_html(
                "Lien invalide", "<h1 class='ko'>Lien invalide</h1><p>Ce match n'existe pas.</p>"
            ),
            status_code=404,
        )

    if match.state != MatchState.DECLINED:
        repo.mark_match_declined(match.id)
        broadcaster.publish(
            match.student_id,
            {"type": "match_declined", "match_id": str(match.id)},
        )

    return HTMLResponse(
        _accept_html(
            "Pas cette fois",
            "<h1>OK, pas celle-là</h1><p>On retire cette offre de tes matches. On continue à chercher.</p>",
        )
    )


async def _relay_to_employer(*, match: Match, student: Student, offer: Offer) -> None:
    """Notify the employer that a student accepted their mission.

    Uses the same SMTP config as the student notifier when available; falls
    back to a log-only path so dev doesn't need to configure anything.
    """
    from .config import get_settings
    from .notifiers.email_smtp import EmailNotifier

    settings = get_settings()
    if not settings.smtp_configured:
        log.info(
            "Employer relay (no SMTP): student %s accepted offer %s (%s)",
            student.email,
            offer.title,
            offer.contact_email,
        )
        return

    notifier = EmailNotifier(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_addr=settings.smtp_from,
        use_tls=settings.smtp_use_tls,
    )
    try:
        await notifier.send_employer_relay(match=match, student=student, offer=offer)
    except Exception:
        log.exception("Employer relay failed for match %s", match.id)


# ---- Company-facing routes ----------------------------------------------


@app.post("/offers", status_code=201, response_model=OfferCreateResponse)
def create_offer(
    payload: OfferCreate, repo: Repository = Depends(get_repository)
) -> OfferCreateResponse:
    """Employer publishes a mission AND gets candidates inline.

    Cold-start problem killer on the employer side: right after submit,
    the HR contact sees the top 5 students already ranked by StudentFlow
    with the explanation for each score. No more "post and wait".

    The offer is stored in the same `offers` table as scraped ones, so the
    MatcherAgent keeps notifying new matches as students sign up. Source is
    `studentjob` (manual entry) — `source_id` is derived from email+title
    so re-submits are idempotent.

    Auto-enrichment: if the employer didn't list skills, we mine them from
    the description with a deterministic vocabulary-matcher. This keeps the
    matching engine useful even when employers write sloppy listings.
    """
    source_id = f"manual:{(payload.contact_email or payload.company).lower()}:{payload.title}"
    enriched_skills = merge_skills(
        payload.skills, extract_skills(f"{payload.title}\n{payload.description}")
    )
    offer = Offer(
        source=Source.STUDENTJOB,
        source_id=source_id,
        title=payload.title,
        description=payload.description,
        company=payload.company,
        city=payload.city,
        remote=payload.remote,
        contract=payload.contract,
        hours_per_week=payload.hours_per_week,
        skills=enriched_skills,
        url=payload.url,
        contact_email=str(payload.contact_email or ""),
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    repo.upsert_offers([offer])

    # Employer-side cold-start: score against every active student and return
    # the top 5 so the HR contact sees value immediately after submit.
    students = repo.list_active_students()
    ranked = rank_students_for_offer(
        offer, students, threshold=get_settings().match_score_threshold
    )
    candidates = [
        StudentMatchOut(
            student_id=student.id,
            full_name=student.full_name,
            email=student.email,
            city=student.city,
            skills=student.skills,
            score=result.score,
            reasons=result.reasons,
            distance_km=result.distance_km,
        )
        for student, result in ranked[:5]
    ]

    return OfferCreateResponse(
        id=offer.id,
        enriched_skills=enriched_skills,
        candidates=candidates,
    )


@app.get("/offers/{offer_id}/matches", response_model=list[StudentMatchOut])
def list_matches_for_offer(
    offer_id: UUID, repo: Repository = Depends(get_repository)
) -> list[StudentMatchOut]:
    """Top students for a given mission, scored on the fly.

    Same engine as the student-side view — we just flip the axis. Employers
    get the best candidates ranked by score, with the reasons attached so
    they can explain why StudentFlow suggested them.
    """
    offer = repo.get_offer(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    students = repo.list_active_students()
    ranked = rank_students_for_offer(
        offer, students, threshold=get_settings().match_score_threshold
    )
    return [
        StudentMatchOut(
            student_id=student.id,
            full_name=student.full_name,
            email=student.email,
            city=student.city,
            skills=student.skills,
            score=result.score,
            reasons=result.reasons,
            distance_km=result.distance_km,
        )
        for student, result in ranked
    ]


# Silence unused-import warning (datetime kept for future routes).
_ = datetime
