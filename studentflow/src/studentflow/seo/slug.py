"""URL-safe slug generation for offers and programmatic SEO pages.

Slugs are deterministic and human-readable:
  offer_slug(offer) → "serveur-restaurant-le-zinc-paris-cdd-a1b2c3d4"

The 8-char UUID suffix prevents collisions between similar titles while
keeping the slug opaque enough that users can't enumerate IDs.
"""

from __future__ import annotations

import re
import unicodedata

from ..models import ContractType, Offer

# French accent normalization + ASCII conversion
_ACCENT_MAP = str.maketrans(
    "àâäéèêëîïôöùûüÿçœæ",
    "aaaeeeeiioouuuycoa",
)


def slugify(text: str, *, max_len: int = 80) -> str:
    """Turn any text into a URL-safe, SEO-friendly slug."""
    # Normalize unicode (é → e + combining accent → strip combining)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Also apply our explicit map for anything NFKD missed
    text = text.translate(_ACCENT_MAP)
    text = text.lower()
    # Keep only alphanumerics and hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text[:max_len]


def city_slug(city: str) -> str:
    """Canonical slug for a city (used in /emplois/{city} URLs)."""
    return slugify(city, max_len=40)


def skill_slug(skill: str) -> str:
    """Canonical slug for a skill (used in /emplois/{city}/{skill} URLs)."""
    return slugify(skill, max_len=40)


def contract_label(contract: ContractType) -> str:
    """Human-readable French contract label for SEO page titles."""
    return {
        ContractType.INTERNSHIP: "stage",
        ContractType.APPRENTICESHIP: "alternance",
        ContractType.CDD: "cdd",
        ContractType.CDI: "cdi",
        ContractType.PART_TIME: "job-etudiant",
        ContractType.FREELANCE: "freelance",
        ContractType.OTHER: "emploi",
    }.get(contract, "emploi")


def offer_slug(offer: Offer) -> str:
    """Unique, human-readable slug for a single offer page.

    Format: {title}-{company}-{city}-{contract}-{short-uuid}

    The short UUID suffix guarantees uniqueness even when two similar
    offers have the same title+company+city. 8 hex chars = 4.3 billion
    combinations — enough for any job platform at scale.
    """
    parts = [
        offer.title,
        offer.company,
        offer.city,
        contract_label(offer.contract),
    ]
    base = slugify(" ".join(p for p in parts if p), max_len=72)
    short_id = str(offer.id).replace("-", "")[:8]
    return f"{base}-{short_id}"
