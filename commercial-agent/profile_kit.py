#!/usr/bin/env python3
"""
Kit de profil freelance multi-plateforme.

Genere les textes de profil adaptes a chaque plateforme de freelance
pour l'inscription et la mise a jour du profil de Baptiste Thevenot.

Usage :
    python profile_kit.py --platform all
    python profile_kit.py --platform codeur --output profil-codeur.txt
    python profile_kit.py --format json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IDENTITY = {
    "first_name": "Baptiste",
    "last_name": "Thevenot",
    "email": "bp.thevenot@gmail.com",
    "company": "SNB Consulting",
    "status": "Entrepreneur Individuel",
    "location_city": "France",
    "location_region": "Ile-de-France / Remote",
    "phone": "A renseigner",
    "experience_years": 8,
    "languages": ["Francais (natif)", "Anglais (professionnel)"],
}

SKILLS = {
    "primary_titles": [
        "Consultant IA & Automatisation",
        "Developpeur Python Senior",
        "Expert CRM & RevOps",
    ],
    "expertise_domains": [
        "Intelligence Artificielle / Agents IA",
        "Automatisation de processus",
        "CRM & RevOps (HubSpot, Salesforce)",
        "Developpement Python",
        "Integration API",
        "Cloud & DevOps",
        "Data Engineering",
    ],
    "technical_skills": [
        "Python", "FastAPI", "asyncio",
        "Claude API (Anthropic)", "OpenAI API", "LangGraph",
        "HubSpot API", "Salesforce API",
        "Gmail API", "Google Workspace",
        "Notion API", "Slack API",
        "PostgreSQL", "pgvector", "Redis",
        "Docker", "Kubernetes",
        "GitHub Actions", "CI/CD",
        "Netlify", "Railway",
        "React", "TypeScript", "HTML/CSS/JS",
        "Shopify API",
    ],
    "soft_skills": [
        "Gestion de projet technique",
        "Communication client directe",
        "Capacite d'analyse metier",
        "Autonomie totale",
        "Livraison iterative rapide",
    ],
}

MISSION_PREFERENCES = {
    "tjm_range": "550 - 900 EUR HT",
    "tjm_standard": 650,
    "availability": "Disponible immediatement",
    "mobility": ["Remote (prioritaire)", "Paris / Ile-de-France (ponctuel)", "France entiere"],
    "preferred_duration": "1 semaine a 6 mois+",
    "max_parallel": 2,
}

PORTFOLIO_HIGHLIGHTS = [
    {
        "name": "Agent commercial autonome (SNB Consulting)",
        "desc": "Pipeline 80k EUR, 777 contacts, routines 24/7, dashboard temps reel",
        "stack": "Python, Claude API, HubSpot, Gmail, Notion, GitHub Actions, Netlify",
    },
    {
        "name": "Mission Responder multi-plateforme",
        "desc": "Generation automatique de reponses adaptees a 10+ plateformes freelance",
        "stack": "Python, Claude API, GitHub Actions",
    },
    {
        "name": "Automatisation CRM HubSpot (client B2B SaaS)",
        "desc": "22 commerciaux, 4000 deals, scoring, sequences outbound, dashboards direction",
        "stack": "HubSpot API, Python, Gmail, Slack",
    },
    {
        "name": "RAG metier industriel",
        "desc": "10k+ documents indexes, recherche semantique sub-seconde, reponses contextualisees",
        "stack": "Python, pgvector, FastAPI, Claude API, Docker",
    },
    {
        "name": "La Francaise des Sauces (LFDS)",
        "desc": "E-commerce premium, quiz interactif B2C, generation de leads restaurateurs",
        "stack": "React, Vite, Netlify, Shopify",
    },
]

HEADLINE = (
    "Consultant Freelance | IA & Automatisation | Python, Claude API, HubSpot | "
    "8 ans d'experience | Agents IA autonomes en production"
)

BIO_SHORT = (
    "Consultant freelance specialise dans la conception d'agents IA autonomes "
    "et l'automatisation de processus commerciaux. 8 ans d'experience dont "
    "les 3 dernieres annees exclusivement dediees a l'orchestration d'agents "
    "Claude et GPT sur des cas metier reels. Je transforme des processus "
    "manuels en systemes autonomes 24h/24 connectes a vos outils existants."
)

BIO_LONG = (
    "Je suis Baptiste Thevenot, consultant freelance chez SNB Consulting.\n\n"
    "Ma specialite : concevoir et deployer des agents IA autonomes qui automatisent "
    "des processus metier reels (prospection commerciale, qualification de leads, "
    "suivi pipeline, reporting). Je ne fais pas de PoC qui restent dans un tiroir, "
    "je livre des systemes en production qui fonctionnent 24h/24.\n\n"
    "Mon parcours : 8 ans de developpement et d'automatisation, dont les 3 dernieres "
    "annees entierement dediees aux agents IA (Claude API, orchestration multi-outils, "
    "bases vectorielles, integrations CRM).\n\n"
    "Ce que je livre :\n"
    "- Agents IA autonomes avec routines programmees (prospection, suivi, audit)\n"
    "- Integrations CRM sur-mesure (HubSpot, Salesforce)\n"
    "- Automatisation email (Gmail API, sequences outbound)\n"
    "- Dashboards temps reel et reporting automatique\n"
    "- Pipelines de qualification et scoring de leads\n"
    "- Systemes RAG metier (bases vectorielles, recherche semantique)\n\n"
    "Stack technique : Python, FastAPI, Claude API (Anthropic), HubSpot, Gmail API, "
    "Notion, Slack, PostgreSQL/pgvector, Docker, Kubernetes, GitHub Actions, Netlify.\n\n"
    "Mon approche : phases courtes avec livrable concret a chaque etape, validation "
    "avant de poursuivre, documentation incluse, astreinte post-livraison."
)


PLATFORMS = {
    "codeur": {
        "name": "Codeur.com",
        "headline": "Developpeur Python Senior | IA & Automatisation | 8 ans d'exp.",
        "bio": BIO_SHORT,
        "categories": ["Developpement Python", "Intelligence Artificielle", "Automatisation", "API / Integration"],
    },
    "malt": {
        "name": "Malt",
        "headline": HEADLINE,
        "bio": BIO_LONG,
        "categories": ["Consultant en automatisation", "Developpeur Python", "Expert CRM", "IA / Machine Learning"],
    },
    "freelance-informatique": {
        "name": "Freelance-Informatique.fr",
        "headline": "Consultant IA & Automatisation Python | 8 ans | Agent IA en production",
        "bio": BIO_LONG,
        "professions": ["Consultant IT", "Developpeur freelance", "Chef de projet informatique"],
        "expertise_domains": ["Cloud & Infrastructure", "Data & AI", "Development"],
        "categories": ["Python", "Intelligence Artificielle", "Automatisation", "CRM", "API"],
    },
    "free-work": {
        "name": "Free-Work (ex Freelance-info)",
        "headline": "Expert Agents IA Python | Automatisation CRM | 8 ans d'experience",
        "bio": BIO_LONG,
        "categories": ["Python", "IA", "DevOps", "CRM", "Automatisation"],
    },
    "upwork": {
        "name": "Upwork",
        "headline": "AI Agent Developer | Python, Claude API, HubSpot Automation | 8 Years Exp.",
        "bio": (
            "I design and deploy autonomous AI agents that automate real business processes. "
            "8 years of development experience, last 3 years focused exclusively on AI agent "
            "orchestration (Claude API, multi-tool agents, vector databases, CRM integrations).\n\n"
            "What I deliver:\n"
            "- Autonomous AI agents with scheduled routines (prospecting, follow-up, audit)\n"
            "- Custom CRM integrations (HubSpot, Salesforce)\n"
            "- Email automation (Gmail API, outbound sequences)\n"
            "- Real-time dashboards and automated reporting\n"
            "- Lead qualification pipelines and scoring\n"
            "- RAG systems (vector databases, semantic search)\n\n"
            "Tech stack: Python, FastAPI, Claude API (Anthropic), HubSpot, Gmail API, "
            "Notion, PostgreSQL/pgvector, Docker, Kubernetes, GitHub Actions.\n\n"
            "Approach: short phases with concrete deliverables, validation before moving forward, "
            "documentation included."
        ),
        "categories": ["Python Development", "AI & Machine Learning", "CRM Automation", "API Integration"],
    },
    "fiverr": {
        "name": "Fiverr",
        "headline": "AI Agent Developer | Python Automation Expert",
        "bio": (
            "I build autonomous AI agents and automation systems that work 24/7.\n"
            "Specialties: Claude API agents, HubSpot CRM automation, email automation, "
            "real-time dashboards, lead scoring pipelines.\n"
            "8 years experience. Fast delivery. Clean code."
        ),
        "categories": ["Python Developer", "AI Services", "CRM Consultant", "Automation"],
    },
    "linkedin": {
        "name": "LinkedIn",
        "headline": HEADLINE,
        "bio": BIO_LONG,
        "categories": [],
    },
    "crealance": {
        "name": "Crealance",
        "headline": "Consultant IA & Automatisation | Python, Claude API, CRM",
        "bio": BIO_SHORT,
        "categories": ["Developpement", "Intelligence Artificielle", "Automatisation"],
    },
    "lehibou": {
        "name": "LeHibou",
        "headline": "Expert Python & IA | Agents autonomes | CRM Automation",
        "bio": BIO_LONG,
        "categories": ["Developpement Python", "IA", "CRM", "DevOps"],
    },
    "kicklox": {
        "name": "Kicklox",
        "headline": "Ingenieur IA & Automatisation | Python Senior | 8 ans",
        "bio": BIO_SHORT,
        "categories": ["Intelligence Artificielle", "Developpement Python", "DevOps", "Data"],
    },
}


def generate_profile(platform: str) -> dict:
    cfg = PLATFORMS.get(platform, PLATFORMS.get("codeur"))
    return {
        "platform": cfg["name"],
        "identity": IDENTITY,
        "headline": cfg["headline"],
        "bio": cfg["bio"],
        "categories": cfg.get("categories", []),
        "professions": cfg.get("professions", SKILLS["primary_titles"]),
        "expertise_domains": cfg.get("expertise_domains", SKILLS["expertise_domains"]),
        "technical_skills": SKILLS["technical_skills"],
        "soft_skills": SKILLS["soft_skills"],
        "mission_preferences": MISSION_PREFERENCES,
        "portfolio": PORTFOLIO_HIGHLIGHTS,
    }


def format_text(profile: dict) -> str:
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  PROFIL FREELANCE - {profile['platform']}")
    lines.append(f"{'=' * 60}")
    lines.append("")

    id_ = profile["identity"]
    lines.append(f"Nom : {id_['first_name']} {id_['last_name']}")
    lines.append(f"Email : {id_['email']}")
    lines.append(f"Societe : {id_['company']}")
    lines.append(f"Localisation : {id_['location_city']} / {id_['location_region']}")
    lines.append(f"Experience : {id_['experience_years']} ans")
    lines.append(f"Langues : {', '.join(id_['languages'])}")
    lines.append("")

    lines.append(f"TITRE / HEADLINE")
    lines.append(profile["headline"])
    lines.append("")

    lines.append("PRESENTATION")
    lines.append(profile["bio"])
    lines.append("")

    if profile["categories"]:
        lines.append("CATEGORIES")
        for c in profile["categories"]:
            lines.append(f"  - {c}")
        lines.append("")

    lines.append("COMPETENCES TECHNIQUES")
    for s in profile["technical_skills"]:
        lines.append(f"  - {s}")
    lines.append("")

    lines.append("TARIFICATION")
    mp = profile["mission_preferences"]
    lines.append(f"  TJM : {mp['tjm_range']}")
    lines.append(f"  TJM standard : {mp['tjm_standard']} EUR HT")
    lines.append(f"  Disponibilite : {mp['availability']}")
    lines.append(f"  Mobilite : {', '.join(mp['mobility'])}")
    lines.append(f"  Duree mission : {mp['preferred_duration']}")
    lines.append("")

    lines.append("PORTFOLIO")
    for p in profile["portfolio"]:
        lines.append(f"  {p['name']}")
        lines.append(f"    {p['desc']}")
        lines.append(f"    Stack : {p['stack']}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les profils freelance multi-plateforme.")
    parser.add_argument(
        "--platform",
        default="all",
        choices=sorted(list(PLATFORMS.keys()) + ["all"]),
    )
    parser.add_argument("--format", default="text", choices=["text", "json"])
    parser.add_argument("--output", default=None, help="Fichier de sortie")
    args = parser.parse_args()

    platforms = list(PLATFORMS.keys()) if args.platform == "all" else [args.platform]
    results = {p: generate_profile(p) for p in platforms}

    if args.format == "json":
        output = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        parts = []
        for p in platforms:
            parts.append(format_text(results[p]))
        output = "\n\n".join(parts)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        sys.stderr.write(f"[profile_kit] Ecrit dans {args.output}\n")
    else:
        sys.stdout.write(output + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
