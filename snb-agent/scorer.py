"""SNB Mission Hunter — Scoring 0-100 avec penalite CDI."""

import logging
from datetime import datetime, timezone
from models import RawMission

logger = logging.getLogger("snb.scorer")

HIGH_VALUE_KEYWORDS = {
    "claude", "anthropic", "shopify", "next.js", "nextjs", "react",
    "ia", "ai", "automatisation", "automation", "agent", "multi-agent",
    "mcp", "chatbot", "scraping", "python",
}

CDI_KEYWORDS = [
    "cdi", "permanent", "full-time employee", "salaire annuel",
    "annual salary", "benefits package", "mutuelle", "conges payes",
    "paid vacation", "w-2", "embauche", "poste fixe", "temps plein",
    "lundi au vendredi", "35h", "39h", "permanent contract",
    "unbefristet", "festanstellung",
]


def classify_mission(mission: RawMission) -> str:
    text = f"{mission.title} {mission.description} {' '.join(str(t) for t in (mission.tags or []) if t)}".lower()
    if any(kw in text for kw in ["ia", "ai", "machine learning", "deep learning",
                                   "chatbot", "gpt", "claude", "llm", "nlp",
                                   "automation", "automatisation", "agent"]):
        return "ia"
    if any(kw in text for kw in ["react", "next", "vue", "angular", "frontend",
                                   "backend", "fullstack", "shopify", "wordpress",
                                   "website", "web app", "site web", "landing"]):
        return "web"
    if any(kw in text for kw in ["data", "scraping", "pipeline", "etl", "sql",
                                   "dashboard", "analytics", "bi", "tableau"]):
        return "data"
    if any(kw in text for kw in ["strategie", "strategy", "consulting", "conseil",
                                   "transformation", "change management", "audit"]):
        return "consulting"
    if any(kw in text for kw in ["design", "branding", "logo", "identite", "ux",
                                   "ui", "figma", "graphique"]):
        return "design"
    return "other"


def is_cdi(mission: RawMission) -> bool:
    """Detect if a mission is actually a CDI/permanent position."""
    text = f"{mission.title} {mission.description}".lower()
    cdi_count = sum(1 for kw in CDI_KEYWORDS if kw in text)
    freelance_signals = ["freelance", "mission", "prestation", "tjm", "taux journalier",
                         "day rate", "contract", "interim", "independant", "contractor"]
    freelance_count = sum(1 for kw in freelance_signals if kw in text)
    return cdi_count >= 2 and freelance_count == 0


def score_mission(mission: RawMission, profile: dict) -> int:
    score = 0
    keywords = profile.get("keywords", [])
    text = f"{mission.title} {mission.description} {' '.join(str(t) for t in (mission.tags or []) if t)}".lower()

    # -- Skill match (0-40) --
    if keywords:
        matches = 0
        high_matches = 0
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in text:
                matches += 1
                if kw_lower in HIGH_VALUE_KEYWORDS:
                    high_matches += 1
        base_ratio = matches / len(keywords)
        high_bonus = min(15, high_matches * 4)
        skill_score = min(40, int(base_ratio * 60) + high_bonus)
        score += skill_score

    # -- Budget match (0-20) --
    tjm_min = profile.get("tjm_min", 350)
    if mission.budget_min is not None and mission.budget_max is not None:
        if mission.budget_min >= tjm_min:
            score += 20
        elif mission.budget_max >= tjm_min:
            score += 12
        elif mission.budget_max >= tjm_min * 0.7:
            score += 5
    elif mission.budget_min is not None:
        score += 15 if mission.budget_min >= tjm_min else 5
    else:
        score += 8

    # -- Freshness (0-20) --
    if mission.posted_at:
        now = datetime.now(timezone.utc)
        posted = mission.posted_at if mission.posted_at.tzinfo else mission.posted_at.replace(tzinfo=timezone.utc)
        age_minutes = (now - posted).total_seconds() / 60
        if age_minutes < 15:
            score += 20
        elif age_minutes < 60:
            score += 16
        elif age_minutes < 180:
            score += 12
        elif age_minutes < 720:
            score += 8
        elif age_minutes < 1440:
            score += 4
    else:
        score += 5

    # -- Remote (0-10) --
    score += 10 if mission.remote else 3

    # -- Client quality (0-10) — placeholder --
    score += 5

    # -- CDI penalty (P2 fix) --
    if is_cdi(mission):
        score = max(0, score - 15)
        logger.debug(f"CDI penalty applied: {mission.title[:50]}")

    return min(100, max(0, score))
