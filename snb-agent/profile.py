"""Profil candidat Baptiste Thevenot.
NE JAMAIS mentionner S&B Consulting dans les propositions.
"""

PROFILE = {
    "name": "Baptiste Thevenot",
    "title": "Consultant Web & IA",
    "tjm": 450,
    "currency": "EUR",
    "location": "Toulouse, France",
    "remote": True,
    "travel_radius_km": 50,
    "languages": ["Francais (natif)", "Anglais (courant)", "Espagnol (courant)"],
    "bio_short": "Consultant freelance specialise en developpement web, intelligence artificielle et automatisation de processus.",
    "bio_full": (
        "Consultant freelance specialise en developpement web, intelligence artificielle "
        "et automatisation de processus. Titulaire d'un Master 2 en Strategie et Conseil "
        "(TBS Toulouse), j'accompagne entreprises et startups dans la creation de sites "
        "performants, l'integration d'outils IA (Claude, OpenAI, n8n) et l'automatisation "
        "de leurs workflows. Experiences internationales et forte culture produit."
    ),
    "skills_primary": ["React.js", "Node.js", "Shopify", "Prompt Engineering", "Strategie digitale", "Claude API", "OpenAI"],
    "skills_secondary": ["HTML/CSS", "JavaScript", "Python", "Figma", "UI/UX Design", "Zapier", "n8n", "Automatisation", "E-commerce"],
    "experience_years": 5,
    "education": "Master 2 Strategie et Conseil — TBS Toulouse Business School",
    "malt_url": "https://www.malt.fr/profile/baptistethevenot1",
    "email": "bp.thevenot@gmail.com",
    "phone": "06 86 50 43 79",
    "siret": "849 022 058",
}

MISSION_TYPE_ANGLES = {
    "ia": "specialiste IA et automatisation (Claude API, OpenAI, agents IA, chatbots, n8n)",
    "web": "developpeur web fullstack (React.js, Next.js, Shopify, Node.js, UI/UX Figma)",
    "data": "specialiste data et automatisation (Python, scraping, dashboards, analytics)",
    "consulting": "consultant en strategie digitale et transformation (Master 2 TBS)",
    "design": "consultant UX/UI et branding (Figma, charte graphique, identite visuelle)",
    "other": "consultant polyvalent Web & IA",
}


def get_proposal_prompt(mission_title, mission_desc, mission_source, mission_type="other", language="auto"):
    lang = language
    if lang == "auto":
        lang = "fr" if any(w in (mission_desc or "").lower() for w in
            ["bonjour", "nous", "recherchons", "entreprise", "projet", "poste"]) else "en"

    p = PROFILE
    skills = ", ".join(p["skills_primary"][:5])
    angle = MISSION_TYPE_ANGLES.get(mission_type, MISSION_TYPE_ANGLES["other"])

    if lang == "fr":
        return f"""Tu es {p['name']}, {angle} freelance base a {p['location']}.
{p['bio_full']}

Competences cles : {skills}
TJM : {p['tjm']}EUR/jour | Langues : FR/EN/ES

MISSION :
Titre : {mission_title}
Source : {mission_source}
Type detecte : {mission_type}
Description : {mission_desc[:2000]}

Redige une proposition de candidature professionnelle et personnalisee.
- Accroche qui montre que tu as compris le besoin du client
- 2-3 points montrant comment tes competences repondent au besoin
- Adapte l'angle selon le type de mission ({mission_type})
- Proposition de valeur concrete (pas de bla-bla)
- Disponibilite et prochaine etape
- Ton professionnel, direct, confiant sans arrogance
- Maximum 200 mots
- NE MENTIONNE JAMAIS "S&B Consulting"
- Signe : Baptiste Thevenot"""
    else:
        return f"""You are {p['name']}, a freelance {angle} based in {p['location']}.
{p['bio_full']}

Key skills: {skills}
Day rate: EUR{p['tjm']}/day | Languages: FR/EN/ES

MISSION:
Title: {mission_title}
Source: {mission_source}
Detected type: {mission_type}
Description: {mission_desc[:2000]}

Write a professional, personalized proposal.
- Hook showing you understand the client's need
- 2-3 points matching your skills to their requirements
- Adapt angle to mission type ({mission_type})
- Concrete value proposition (no fluff)
- Availability and next step
- Professional, direct, confident tone
- Maximum 200 words
- NEVER mention "S&B Consulting"
- Sign: Baptiste Thevenot"""
