#!/usr/bin/env python3
"""
Mission responder - genere des reponses de mission pour plateformes freelance.

Usage :
    python mission_responder.py \\
        --platform codeur \\
        --budget "3000 EUR" \\
        --urgency "demarrage sous 2 semaines" \\
        --output docs/missions/mission-xyz.md \\
        < mission.txt

    echo "Je cherche un dev Python pour..." | python mission_responder.py --platform malt

Peut etre utilise :
- En CLI locale par Baptiste
- Dans un GitHub Actions workflow (via workflow_dispatch inputs)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

from mission_prompts import (
    BAPTISTE_PROFILE,
    PLATFORM_CONFIG,
    build_system_prompt,
    build_user_message,
)

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 2000
TEMPERATURE = 0.4

MISSIONS_DIR = Path("docs/missions")
INDEX_FILE = MISSIONS_DIR / "index.json"


def slugify(text: str, max_len: int = 60) -> str:
    """Convertit un texte en slug URL-safe."""
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"[-\s]+", "-", t).strip("-")
    return t[:max_len] or "mission"


def extract_title(mission_text: str) -> str:
    """Extrait un titre court de la mission pour le slug et l'index."""
    first_line = mission_text.strip().split("\n")[0][:80]
    return first_line.strip() or "Mission sans titre"


def call_claude(system_prompt: str, user_message: str) -> str:
    """Appelle Claude via l'API Anthropic."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.stderr.write(
            "ERREUR : variable d'environnement ANTHROPIC_API_KEY manquante.\n"
        )
        sys.exit(2)

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    chunks = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    return "".join(chunks).strip()


def sanitize_output(text: str) -> str:
    """Nettoie la sortie : retire emojis/caracteres decoratifs, normalise sauts de ligne."""
    cleaned = []
    for ch in text:
        cp = ord(ch)
        if cp < 128:
            cleaned.append(ch)
            continue
        # Lettres accentuees francaises courantes : on garde
        if cp in range(0x00C0, 0x0180):
            cleaned.append(ch)
            continue
        # Guillemets typographiques -> ASCII
        if ch in "\u2018\u2019":
            cleaned.append("'")
            continue
        if ch in "\u201C\u201D":
            cleaned.append('"')
            continue
        if ch == "\u2013" or ch == "\u2014":
            cleaned.append("-")
            continue
        if ch == "\u2026":
            cleaned.append("...")
            continue
        if ch in "\u20AC":  # euro
            cleaned.append("EUR")
            continue
        # Espace insecable, puces -> fallback
        if ch in "\u00A0":
            cleaned.append(" ")
            continue
        if ch in "\u2022\u25CF":
            cleaned.append("-")
            continue
        # Tout le reste (emojis, symboles) : on drop
    out = "".join(cleaned)
    # Normalise les sauts de ligne multiples
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def save_response(
    slug: str,
    title: str,
    platform: str,
    mission_text: str,
    response_text: str,
    budget_hint: str,
    urgency: str,
) -> Path:
    """Sauvegarde la reponse en markdown dans docs/missions/."""
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{ts}-{platform}-{slug}.md"
    path = MISSIONS_DIR / filename

    front_matter = {
        "id": filename.replace(".md", ""),
        "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": platform,
        "title": title,
        "budget_hint": budget_hint,
        "urgency": urgency,
    }

    content = "---\n"
    for k, v in front_matter.items():
        content += f"{k}: {json.dumps(v, ensure_ascii=True)}\n"
    content += "---\n\n"
    content += "## Mission (extrait)\n\n"
    content += "```\n" + mission_text.strip()[:1500] + "\n```\n\n"
    content += "## Reponse generee\n\n"
    content += response_text + "\n"

    path.write_text(content, encoding="utf-8")
    return path


def update_index(entry: dict) -> None:
    """Ajoute l'entree au fichier d'index JSON."""
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = []
    index.insert(0, entry)
    # Garde les 200 dernieres entrees
    index = index[:200]
    INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=True, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere une reponse de mission.")
    parser.add_argument(
        "--platform",
        required=True,
        choices=sorted(PLATFORM_CONFIG.keys()),
        help="Plateforme cible (codeur, malt, upwork, ...)",
    )
    parser.add_argument(
        "--budget",
        default="",
        help="Budget indicatif communique par le client (ex : '3000 EUR')",
    )
    parser.add_argument(
        "--urgency", default="", help="Indication d'urgence ou de delai"
    )
    parser.add_argument(
        "--mission-file",
        default=None,
        help="Chemin vers un fichier mission. Sinon lu depuis stdin.",
    )
    parser.add_argument(
        "--save", action="store_true", help="Sauvegarde la reponse dans docs/missions/"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Chemin de sortie alternatif pour la reponse (ecrit aussi stdout).",
    )
    args = parser.parse_args()

    if args.mission_file:
        mission_text = Path(args.mission_file).read_text(encoding="utf-8")
    else:
        mission_text = sys.stdin.read()

    mission_text = mission_text.strip()
    if not mission_text:
        sys.stderr.write("ERREUR : mission vide.\n")
        return 1

    system_prompt = build_system_prompt(args.platform)
    user_message = build_user_message(mission_text, args.budget, args.urgency)

    sys.stderr.write(
        f"[mission_responder] Generation pour {args.platform} "
        f"(budget={args.budget or 'non precise'})...\n"
    )
    t0 = time.time()
    raw_response = call_claude(system_prompt, user_message)
    elapsed = time.time() - t0
    response = sanitize_output(raw_response)

    sys.stderr.write(
        f"[mission_responder] OK - {len(response)} chars - {elapsed:.1f}s\n"
    )

    # Sortie standard
    sys.stdout.write(response + "\n")

    # Sauvegarde optionnelle
    if args.save or args.output:
        title = extract_title(mission_text)
        slug = slugify(title)
        path = save_response(
            slug=slug,
            title=title,
            platform=args.platform,
            mission_text=mission_text,
            response_text=response,
            budget_hint=args.budget,
            urgency=args.urgency,
        )
        sys.stderr.write(f"[mission_responder] Sauvegarde : {path}\n")

        update_index(
            {
                "id": path.stem,
                "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "platform": args.platform,
                "platform_name": PLATFORM_CONFIG[args.platform]["name"],
                "title": title,
                "budget_hint": args.budget,
                "urgency": args.urgency,
                "file": path.name,
                "preview": response[:200],
            }
        )

        if args.output:
            Path(args.output).write_text(response, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
