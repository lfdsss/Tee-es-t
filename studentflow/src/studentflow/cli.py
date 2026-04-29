"""Command-line entry point.

Commands:
    studentflow run-api       Start the FastAPI HTTP server.
    studentflow run-agents    Start the 3 agent loops forever.
    studentflow tick          Run ONE pass of each agent and exit. Useful to
                              validate the full pipeline in CI or just after
                              deploy, without waiting for the default intervals.
    studentflow seed-demo     Insert a couple of demo students into the repo
                              so you can immediately test /students/{id}/matches.

All commands auto-pick the repository:
    - SupabaseRepository if SUPABASE_URL + SUPABASE_SERVICE_KEY are set
    - InMemoryRepository otherwise (safe for dev / first-run smoke test)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date

from .agents import MatcherAgent, NotifierAgent, ScraperAgent, run_forever
from .config import get_settings
from .db import InMemoryRepository, Repository, SupabaseRepository
from .models import ContractType, Student

log = logging.getLogger("studentflow.cli")


def _build_repo() -> Repository:
    settings = get_settings()
    if settings.supabase_configured:
        log.info("Using SupabaseRepository")
        return SupabaseRepository(settings)
    log.warning("Supabase not configured — falling back to in-memory repository")
    return InMemoryRepository()


async def _tick_once(repo: Repository) -> None:
    """Run one pass of each agent sequentially. Handy for deploy smoke tests."""
    settings = get_settings()

    scraper = ScraperAgent(repo)
    scraped = await scraper.tick()
    log.info("Scraper tick: %d offers upserted", scraped)

    matcher = MatcherAgent(repo, threshold=settings.match_score_threshold)
    created = await matcher.tick()
    log.info("Matcher tick: %d matches created", created)

    notifier = NotifierAgent(repo, webhook_url=settings.notification_webhook_url)
    sent = await notifier.tick()
    log.info("Notifier tick: %d notifications processed", sent)


def _seed_demo(repo: Repository) -> None:
    """Insert two demo students covering typical French profiles."""
    if not hasattr(repo, "insert_student"):
        raise SystemExit(
            "This repository does not support insert_student. "
            "Use SupabaseRepository or InMemoryRepository."
        )

    students = [
        Student(
            email="lucas.demo@studentflow.fr",
            full_name="Lucas Demo",
            city="Lyon",
            remote_ok=True,
            skills=["marketing", "seo", "community management", "réseaux sociaux"],
            accepted_contracts=[ContractType.APPRENTICESHIP, ContractType.INTERNSHIP],
            max_hours_per_week=35,
            available_from=date.today(),
        ),
        Student(
            email="sarah.demo@studentflow.fr",
            full_name="Sarah Demo",
            city="Toulouse",
            remote_ok=False,
            skills=["vente", "accueil client", "caisse"],
            accepted_contracts=[ContractType.PART_TIME, ContractType.CDD],
            max_hours_per_week=15,
            available_from=date.today(),
        ),
    ]
    for s in students:
        repo.insert_student(s)  # type: ignore[attr-defined]
        log.info("Seeded demo student %s (%s)", s.full_name, s.id)
    log.info("Done. %d demo students inserted.", len(students))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="studentflow")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-agents", help="Start the 3 agent loops")

    run_api = sub.add_parser("run-api", help="Start the FastAPI server")
    run_api.add_argument("--host", default=None)
    run_api.add_argument("--port", type=int, default=None)

    sub.add_parser("tick", help="Run ONE pass of each agent and exit")
    sub.add_parser("seed-demo", help="Insert demo students into the current repository")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    if args.command == "run-agents":
        repo = _build_repo()
        asyncio.run(run_forever(repo))
        return 0

    if args.command == "run-api":
        import uvicorn

        settings = get_settings()
        uvicorn.run(
            "studentflow.api:app",
            host=args.host or settings.api_host,
            port=args.port or settings.api_port,
            reload=False,
        )
        return 0

    if args.command == "tick":
        repo = _build_repo()
        asyncio.run(_tick_once(repo))
        return 0

    if args.command == "seed-demo":
        repo = _build_repo()
        _seed_demo(repo)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
