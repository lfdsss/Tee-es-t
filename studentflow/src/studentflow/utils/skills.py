"""Rule-based skill extraction.

Zero-dependency extractor that turns a free-text job description into a
normalised list of skills. We keep it deterministic and fast because the
matcher runs it inline when an employer posts a mission without explicit
skills — LLMs would add latency + cost + non-determinism for no real gain
at this size of vocabulary.

The vocabulary is intentionally small and French-job-market aware. Add
terms as the platform grows; each term maps to a canonical, lowercase form.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Canonical skill → list of matching surface forms (lowercased, word-boundary).
# Keep the canonical form identical to how students type it in the signup form
# so Jaccard similarity stays honest.
_SKILL_VOCABULARY: dict[str, list[str]] = {
    # tech
    "python": ["python"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "node": ["node", "nodejs", "node.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],
    "sql": ["sql", "mysql", "postgres", "postgresql"],
    "nosql": ["nosql", "mongodb", "redis"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "sass", "scss", "tailwind"],
    "php": ["php", "laravel", "symfony"],
    "java": ["java", "spring"],
    "c#": ["c#", "csharp", ".net", "dotnet"],
    "git": ["git", "github", "gitlab"],
    "docker": ["docker", "container"],
    "aws": ["aws", "amazon web services"],
    "excel": ["excel", "tableur"],
    "power bi": ["power bi", "powerbi"],
    # marketing / comms
    "community management": ["community management", "community manager", "réseaux sociaux"],
    "social media": ["social media", "instagram", "tiktok", "linkedin", "facebook"],
    "canva": ["canva"],
    "photoshop": ["photoshop"],
    "video": ["video", "vidéo", "montage"],
    "rédaction": ["rédaction", "copywriting", "redaction"],
    "seo": ["seo", "référencement"],
    # commerce / support
    "vente": ["vente", "sales", "commercial", "b2b", "b2c"],
    "service client": ["service client", "sav", "support", "customer service"],
    "accueil": ["accueil", "réception"],
    "téléphone": ["téléphone", "standard", "phoning"],
    # métiers étudiants classiques
    "restauration": ["restauration", "serveur", "serveuse", "barman", "barista"],
    "livraison": ["livraison", "coursier"],
    "baby-sitting": ["baby-sitting", "babysitting", "garde d'enfants"],
    "soutien scolaire": ["soutien scolaire", "tutorat", "cours particuliers"],
    "manutention": ["manutention", "logistique", "entrepôt"],
    "caisse": ["caisse", "mise en rayon"],
    # langues
    "anglais": ["anglais", "english"],
    "espagnol": ["espagnol", "spanish"],
    "allemand": ["allemand", "german"],
    "italien": ["italien", "italian"],
    # data / bureautique
    "google sheets": ["google sheets", "sheets"],
    "notion": ["notion"],
    "figma": ["figma"],
}


def _compile_patterns() -> list[tuple[str, re.Pattern[str]]]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for canonical, surface_forms in _SKILL_VOCABULARY.items():
        escaped = [re.escape(sf) for sf in surface_forms]
        # Word-boundary match, case-insensitive. Keep punctuation-friendly via
        # manual boundaries so "react.js" doesn't get swallowed by \b.
        joined = "|".join(escaped)
        pattern = re.compile(rf"(?<![a-zA-Z0-9]){joined}(?![a-zA-Z0-9])", re.IGNORECASE)
        patterns.append((canonical, pattern))
    return patterns


_PATTERNS = _compile_patterns()


def extract_skills(text: str, *, limit: int = 15) -> list[str]:
    """Return canonical skills detected in `text`, deduped, capped at `limit`.

    Runs in O(|vocab| · |text|) per call. Safe to call inline in request
    handlers at this vocabulary size.
    """
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for canonical, pattern in _PATTERNS:
        if pattern.search(text) and canonical not in seen:
            seen.add(canonical)
            found.append(canonical)
            if len(found) >= limit:
                break
    return found


def merge_skills(existing: Iterable[str], extracted: Iterable[str]) -> list[str]:
    """Combine an existing skill list with auto-extracted ones, deduped."""
    out: list[str] = []
    seen: set[str] = set()
    for s in list(existing) + list(extracted):
        norm = s.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


# Public canonical skill list — used by the frontend autocomplete to show
# students the exact vocabulary the matcher understands. Sorted for stable UX.
VOCABULARY: list[str] = sorted(_SKILL_VOCABULARY.keys())
