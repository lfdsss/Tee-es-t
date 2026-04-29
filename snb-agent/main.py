"""SNB Mission Hunter — Point d'entree principal.
P0 FIX: Agent state shared via Supabase agent_status table.
P0 FIX: SMTP tested at startup.
P1: Mission type passed to proposer for template selection.
P2: CDI penalty in scorer.
"""

import asyncio
import logging
import sys
import time
import signal
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config, PROFILES
from db import Database
from scorer import score_mission, classify_mission
from proposer import Proposer
from notifier import notify_telegram, send_email_digest
from email_sender import send_proposal_email, test_smtp_connection
from api import app, set_db

# Scrapers
from scrapers.remoteok import RemoteOKScraper
from scrapers.remotive import RemotiveScraper
from scrapers.jobicy import JobicyScraper
from scrapers.weworkremotely import WeWorkRemotelyScraper
from scrapers.himalayas import HimalayasScraper
from scrapers.arbeitnow import ArbeitnowScraper
from scrapers.linkedin import LinkedInScraper
from scrapers.workingnomads import WorkingNomadsScraper
from scrapers.codeur import CodeurScraper
from scrapers.talentfr import TalentFRScraper
from scrapers.freework import FreeWorkScraper
from scrapers.guru import GuruScraper
from scrapers.landingjobs import LandingJobsScraper
from scrapers.freelancercom import FreelancerComScraper


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger("snb.main")

SCRAPERS_TIER1 = [
    RemoteOKScraper(), RemotiveScraper(), JobicyScraper(),
    WeWorkRemotelyScraper(), HimalayasScraper(), ArbeitnowScraper(),
    LinkedInScraper(), WorkingNomadsScraper(), CodeurScraper(),
    TalentFRScraper(), FreeWorkScraper(),
]

SCRAPERS_TIER2 = [
    GuruScraper(), LandingJobsScraper(), FreelancerComScraper(),
]

ALL_SCRAPERS = SCRAPERS_TIER1 + SCRAPERS_TIER2

# Globals
config: Config = None
db: Database = None
proposer: Proposer = None
scheduler: AsyncIOScheduler = None
smtp_ok: bool = False

# Counters for agent_status (P0 fix)
_scans_total = 0
_missions_total = 0
_proposals_total = 0
_digest_buffer = []


def _update_agent_status(**extra):
    """Push agent state to Supabase so /health can read it."""
    global _scans_total, _missions_total, _proposals_total
    if db:
        db.update_agent_status({
            "scans_total": _scans_total,
            "missions_total": _missions_total,
            "proposals_total": _proposals_total,
            "last_scan_at": datetime.now(timezone.utc).isoformat(),
            **extra,
        })


async def run_scraper(scraper):
    global _scans_total, _missions_total, _proposals_total, _digest_buffer

    source_name = scraper.name
    start_time = time.time()
    log_id = None

    try:
        try:
            log_id = db.log_scan_start(source_name)
        except Exception as e:
            logger.debug(f"Scan log start failed: {e}")

        raw_missions = await scraper.safe_fetch()
        missions_found = len(raw_missions)

        if not raw_missions:
            _scans_total += 1
            _update_agent_status()
            if log_id:
                duration_ms = int((time.time() - start_time) * 1000)
                db.log_scan_end(log_id, "success", 0, 0, duration_ms=duration_ms)
            return

        profile = PROFILES.get(config.active_profile, PROFILES["baptiste"])
        missions_new = 0

        for raw in raw_missions:
            if db.mission_exists(raw.dedup_key):
                continue

            mission_score = score_mission(raw, profile)
            mission_type = classify_mission(raw)
            db_data = raw.to_db_dict(score=mission_score, mission_type=mission_type)
            inserted = db.insert_mission(db_data)

            if not inserted:
                continue

            missions_new += 1
            _missions_total += 1
            mission_id = inserted["id"]

            logger.info(f"[{source_name}] Nouvelle mission (score {mission_score}): {raw.title[:60]}")

            if mission_score >= config.score_threshold and proposer:
                try:
                    proposal = proposer.generate(raw, mission_type=mission_type)
                    if proposal:
                        proposal.mission_id = mission_id
                        proposal_inserted = db.insert_proposal(proposal.to_db_dict())
                        if proposal_inserted:
                            db.update_mission(mission_id, {
                                "status": "proposal_ready",
                                "proposal_id": proposal_inserted["id"],
                            })
                            _proposals_total += 1
                            await notify_telegram(inserted, proposal.text, config)

                            if smtp_ok and config.email_to:
                                send_proposal_email(
                                    config,
                                    to_email=config.email_to,
                                    subject=f"Nouvelle proposition — {raw.title[:50]}",
                                    body_html=f"""<div style="font-family:sans-serif;max-width:600px">
<h2 style="color:#2563eb">{raw.title}</h2>
<p style="color:#666">{raw.company or 'N/A'} — {raw.source} — Score {mission_score}/100</p>
<div style="background:#f8f5ff;border:1px solid #e4daff;border-radius:10px;padding:16px;margin:16px 0">
<h4 style="color:#7c3aed">Proposition generee</h4>
<pre style="font-family:sans-serif;font-size:14px;line-height:1.6;white-space:pre-wrap">{proposal.text}</pre>
</div>
<p><a href="{raw.source_url}" style="color:#2563eb">Voir l'offre</a> —
<a href="https://snb-consulting-platform.netlify.app" style="color:#2563eb">Dashboard</a></p>
</div>""",
                                )

                            _digest_buffer.append(inserted)
                            logger.info(f"[{source_name}] Proposition generee: {raw.title[:50]}")
                except Exception as e:
                    logger.error(f"Proposal/notify error for {raw.title[:40]}: {e}")

        _scans_total += 1
        _update_agent_status()

        if log_id:
            duration_ms = int((time.time() - start_time) * 1000)
            db.log_scan_end(log_id, "success", missions_found, missions_new, duration_ms=duration_ms)

        if missions_new > 0:
            logger.info(f"[{source_name}] Scan: {missions_new} nouvelles / {missions_found} trouvees")

    except Exception as e:
        logger.error(f"[{source_name}] ERREUR: {e}", exc_info=True)
        if log_id:
            duration_ms = int((time.time() - start_time) * 1000)
            db.log_scan_end(log_id, "error", error_message=str(e), duration_ms=duration_ms)


async def run_email_digest():
    global _digest_buffer
    if _digest_buffer and smtp_ok:
        try:
            send_email_digest(_digest_buffer, config)
            _digest_buffer = []
        except Exception as e:
            logger.error(f"Email digest error: {e}")


def setup_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")

    for scraper in SCRAPERS_TIER1:
        scheduler.add_job(
            run_scraper, IntervalTrigger(seconds=config.scan_interval_fast),
            args=[scraper], id=f"scraper_{scraper.name}", name=f"Scrape {scraper.name}",
            next_run_time=datetime.now(timezone.utc), misfire_grace_time=60, max_instances=1,
        )

    for scraper in SCRAPERS_TIER2:
        scheduler.add_job(
            run_scraper, IntervalTrigger(seconds=config.scan_interval_slow),
            args=[scraper], id=f"scraper_{scraper.name}", name=f"Scrape {scraper.name}",
            next_run_time=datetime.now(timezone.utc), misfire_grace_time=120, max_instances=1,
        )

    scheduler.add_job(run_email_digest, IntervalTrigger(hours=2), id="email_digest", name="Email Digest")

    return scheduler


async def main():
    global config, db, proposer, smtp_ok

    setup_logging()
    logger.info("=" * 60)
    logger.info("SNB Mission Hunter v2 — Demarrage")
    logger.info("=" * 60)

    config = Config.from_env()
    errors = config.validate()
    if errors:
        logger.error(f"Variables manquantes: {', '.join(errors)}")
        sys.exit(1)

    logger.info(f"Config chargee — Profil: {config.active_profile}, Seuil: {config.score_threshold}")

    db = Database(config.supabase_url, config.supabase_service_key)
    set_db(db)
    logger.info("Supabase connecte")

    if config.anthropic_api_key:
        proposer = Proposer(config.anthropic_api_key)
        logger.info("Proposer Claude API initialise")

    # P0: Test SMTP at startup
    smtp_ok = test_smtp_connection(config)
    if smtp_ok:
        logger.info("SMTP Gmail OK")
    else:
        logger.warning("SMTP non disponible — emails desactives")

    # P0: Initial agent status
    _update_agent_status(status="running")

    sched = setup_scheduler()
    sched.start()
    logger.info(f"Scheduler demarre — {len(sched.get_jobs())} jobs")

    # Telegram startup
    try:
        import aiohttp
        if config.telegram_bot_token and config.telegram_chat_id:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": config.telegram_chat_id,
                        "text": f"SNB Mission Hunter v2 demarre\nSources: {len(ALL_SCRAPERS)}\nSeuil: {config.score_threshold}\nSMTP: {'OK' if smtp_ok else 'OFF'}",
                        "parse_mode": "Markdown",
                    },
                )
    except Exception:
        pass

    logger.info("Agent en cours d'execution...")

    stop_event = asyncio.Event()
    def handle_signal(*_):
        logger.info("Signal d'arret recu...")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_event_loop().add_signal_handler(sig, handle_signal)

    await stop_event.wait()
    sched.shutdown(wait=False)
    _update_agent_status(status="stopped")
    logger.info("Agent arrete proprement.")


if __name__ == "__main__":
    asyncio.run(main())
