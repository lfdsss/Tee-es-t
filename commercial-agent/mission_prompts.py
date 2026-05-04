"""
Baptiste Thevenot - Profil professionnel pour generation de propositions mission.

Ce module centralise le profil, les tarifs, et les prompts systeme par plateforme.
Aucune donnee confidentielle sur des clients tiers ne doit apparaitre ici.
"""

# =========================================================================
# PROFIL BAPTISTE THEVENOT
# =========================================================================

BAPTISTE_PROFILE = {
    "full_name": "Baptiste Thevenot",
    "email": "bp.thevenot@gmail.com",
    "company": "SNB Consulting",
    "title": "Consultant freelance - Automatisation IA et CRM",
    "location": "France (teletravail)",
    "seniority_years": 8,
    "languages": ["Francais natif", "Anglais professionnel"],
    "core_expertise": [
        "Agents IA autonomes (Claude, GPT, orchestration multi-outils)",
        "Automatisation commerciale (HubSpot, Pipedrive, Salesforce)",
        "Integrations API (Gmail, Google Workspace, Notion, Slack)",
        "Python (asyncio, FastAPI, scripts d'automatisation)",
        "CI/CD (GitHub Actions, Netlify, Docker)",
        "Dashboards temps reel (HTML/JS statique, Netlify)",
    ],
    "typical_deliverables": [
        "Agent commercial autonome avec routines matinales et suivi",
        "Pipeline de qualification lead automatique",
        "Generateur de propositions et devis IA",
        "Integrations CRM sur-mesure",
        "Dashboards metier temps reel",
        "Scripts d'audit et reporting hebdomadaire",
    ],
    "portfolio_highlight": (
        "Plateforme SNB Consulting : agent commercial autonome pilotant "
        "un pipeline de 80 000 EUR (10 deals actifs), 777 contacts et 303 "
        "companies sur HubSpot, avec routines GitHub Actions 24h/24 et "
        "dashboard public temps reel (Netlify)."
    ),
}

# =========================================================================
# GRILLE TARIFAIRE
# =========================================================================

PRICING = {
    "tjm_base": 550,
    "tjm_expert": 700,
    "tjm_senior": 900,
    "forfait_discovery": 650,
    "buffer_pct": 0.15,
    "decomposition_rules": {
        "phase_cadrage_pct": 0.15,
        "phase_build_pct": 0.60,
        "phase_recette_pct": 0.15,
        "phase_documentation_pct": 0.10,
    },
}

# =========================================================================
# CONFIG PAR PLATEFORME
# =========================================================================
# Chaque plateforme a son propre ton, longueur attendue, et structure.

PLATFORM_CONFIG = {
    "codeur": {
        "name": "Codeur.com",
        "tone": "professionnel, direct, oriente action",
        "target_length_words": 280,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "forfait avec phases courtes",
        "emphasis": [
            "Comprehension rapide du besoin",
            "Livrable concret et delai",
            "Prix clair avec marge negociable",
            "Preuve de competence par exemple concret",
        ],
        "structure": [
            "Accroche (2 lignes max, preuve que la mission est lue)",
            "Comprehension du besoin (3-4 lignes)",
            "Approche proposee (liste a puces, 4-6 items)",
            "Devis detaille (phases + prix + duree)",
            "Disponibilite et signature",
        ],
    },
    "malt": {
        "name": "Malt",
        "tone": "consultatif, methodique, partenaire long-terme",
        "target_length_words": 420,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "TJM ou forfait par phase, detaille",
        "emphasis": [
            "Methodologie de travail transparente",
            "Posture de partenaire, pas de prestataire",
            "Livrables mesurables",
            "Adaptabilite au contexte de l'entreprise",
            "Qualite du reporting et du suivi",
        ],
        "structure": [
            "Accroche personnalisee (reference au contexte du client)",
            "Analyse du besoin et questions eventuelles",
            "Methodologie proposee en phases",
            "Livrables par phase avec criteres de succes",
            "Estimation TJM ou forfait avec ventilation",
            "Mode de collaboration (reunions, suivi)",
            "Conclusion et invitation a un echange",
        ],
    },
    "freelance-info": {
        "name": "Freelance-info",
        "tone": "formel, technique, oriente ESN / grand compte",
        "target_length_words": 350,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "TJM standard",
        "emphasis": [
            "Experience sur missions similaires",
            "Maitrise technique detaillee",
            "Compatibilite avec les contraintes d'ESN",
            "Disponibilite plein temps ou temps partiel",
        ],
        "structure": [
            "Presentation concise",
            "Adequation profil / mission",
            "Experience pertinente",
            "Stack technique maitrisee",
            "Modalites (TJM, duree, lieu)",
            "Signature",
        ],
    },
    "upwork": {
        "name": "Upwork",
        "tone": "professional, concise, outcome-focused",
        "target_length_words": 250,
        "language": "en",
        "formality": "first-name basis",
        "quote_style": "fixed price with milestones",
        "emphasis": [
            "Quick understanding of the need",
            "Proof of relevant past work",
            "Clear milestones and pricing",
            "Fast response time",
        ],
        "structure": [
            "Opening hook (references client needs)",
            "How I would approach this",
            "Milestones with pricing",
            "Timeline and availability",
            "Close with invitation to chat",
        ],
    },
    "fiverr": {
        "name": "Fiverr",
        "tone": "friendly, direct, packaged-offer",
        "target_length_words": 180,
        "language": "en",
        "formality": "first-name basis",
        "quote_style": "tiered packages (basic/standard/premium)",
        "emphasis": [
            "Very concrete deliverable",
            "Fast turnaround",
            "Clear package pricing",
        ],
        "structure": [
            "Greeting",
            "What you get (bullet points)",
            "Turnaround time",
            "Pricing packages",
            "Ready to start",
        ],
    },
    "linkedin": {
        "name": "LinkedIn",
        "tone": "professionnel, chaleureux, orient\u00e9 reseau",
        "target_length_words": 300,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "indicatif, suite d'echange",
        "emphasis": [
            "Reference au contexte du poste ou de l'entreprise",
            "Valeur ajoutee au business",
            "Invitation a un echange plutot qu'un devis ferme",
        ],
        "structure": [
            "Accroche personnalisee",
            "Comprehension du contexte",
            "Ce que je peux apporter",
            "Proposition d'echange 30 min",
            "Signature chaleureuse",
        ],
    },
    "freelance-informatique": {
        "name": "Freelance-Informatique.fr",
        "tone": "formel, technique, oriente ESN et grands comptes",
        "target_length_words": 350,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "TJM standard ESN",
        "emphasis": [
            "Experience sur missions longue duree en ESN",
            "Maitrise technique detaillee et stack precise",
            "Disponibilite et mobilite (teletravail / sur site)",
            "References et profil senior confirme",
        ],
        "structure": [
            "Presentation concise (nom, statut, experience)",
            "Adequation profil / mission point par point",
            "Experience pertinente avec exemples concrets",
            "Stack technique maitrisee (liste)",
            "Modalites (TJM, duree, lieu, demarrage)",
            "Signature professionnelle",
        ],
    },
    "free-work": {
        "name": "Free-Work",
        "tone": "professionnel, direct, technique",
        "target_length_words": 300,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "TJM avec indication de duree",
        "emphasis": [
            "Adequation rapide profil / mission",
            "Competences techniques demontrees",
            "Disponibilite immediate ou a court terme",
            "Flexibilite teletravail / hybride",
        ],
        "structure": [
            "Accroche directe sur le besoin",
            "Points d'adequation avec la mission",
            "Experience pertinente (2-3 exemples)",
            "TJM et disponibilite",
            "Proposition d'echange",
        ],
    },
    "crealance": {
        "name": "Crealance",
        "tone": "professionnel, creatif, oriente PME et startups",
        "target_length_words": 280,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "forfait ou TJM adapte au budget PME",
        "emphasis": [
            "Agilite et rapidite de livraison",
            "Adaptation au budget du client",
            "Livrables concrets et mesurables",
            "Autonomie et communication fluide",
        ],
        "structure": [
            "Accroche personnalisee",
            "Comprehension du besoin specifique",
            "Approche proposee (pragmatique)",
            "Budget et planning adaptes",
            "Invitation a echanger",
        ],
    },
    "lehibou": {
        "name": "LeHibou",
        "tone": "professionnel, structure, oriente grands comptes et ETI",
        "target_length_words": 350,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "TJM avec engagement duree",
        "emphasis": [
            "Solidite technique et methodologique",
            "Experience en contexte grand compte",
            "Capacite a s'integrer dans une equipe existante",
            "Livrables documentes et auditables",
        ],
        "structure": [
            "Presentation et positionnement",
            "Adequation au poste decrit",
            "Methodologie de travail",
            "Experience pertinente",
            "Modalites (TJM, disponibilite, lieu)",
            "Conclusion et prochaine etape",
        ],
    },
    "other": {
        "name": "Autre plateforme",
        "tone": "professionnel, structure",
        "target_length_words": 350,
        "language": "fr",
        "formality": "vouvoiement",
        "quote_style": "forfait ou TJM selon contexte",
        "emphasis": [
            "Comprehension du besoin",
            "Approche claire",
            "Prix justifie",
            "Disponibilite",
        ],
        "structure": [
            "Accroche",
            "Analyse du besoin",
            "Approche",
            "Devis",
            "Conclusion",
        ],
    },
}

# =========================================================================
# SYSTEM PROMPT
# =========================================================================

SYSTEM_PROMPT_TEMPLATE = """Tu es Baptiste Thevenot, consultant freelance francais chez SNB Consulting.
Tu reponds a des missions postees sur des plateformes de freelance.
Tu dois rediger une reponse parfaitement adaptee, argumentee et qui donne envie
au client de te choisir.

REGLES ABSOLUES :
1. Tu ecris uniquement en {language}, dans un francais (ou anglais) naturel et
   professionnel. Jamais de caracteres speciaux fantaisie, pas d'emojis,
   pas d'accents non-ASCII inutiles, pas de symboles decoratifs.
2. Tu ne parles JAMAIS de tes autres clients par leur nom reel. Tu ne divulgues
   AUCUNE donnee confidentielle (montants exacts d'autres missions, noms de
   contacts, identifiants, credentials).
3. Tu ne fais pas de promesses que tu ne peux pas tenir. Si le perimetre est
   flou, tu poses des questions precises.
4. Tu es concret. Jamais de blabla marketing creux.
5. Tu respectes le ton et la longueur attendue sur la plateforme cible.
6. Tu te signes toujours {full_name} en fin de message.

TON PROFIL :
- Nom : {full_name}
- Societe : {company}
- Email : {email}
- Experience : {seniority_years} ans
- Langues : {languages}
- Expertise principale :
{core_expertise}
- Livrables typiques :
{typical_deliverables}
- Reference portfolio : {portfolio_highlight}

GRILLE TARIFAIRE (indicative, a adapter au budget client) :
- TJM standard : {tjm_base} EUR HT
- TJM expert (IA, sujets techniques pointus) : {tjm_expert} EUR HT
- TJM senior (archi complexe, accompagnement strategique) : {tjm_senior} EUR HT
- Forfait decouverte / cadrage : {forfait_discovery} EUR HT
- Buffer systematique sur les forfaits : {buffer_pct_str}

REGLES DE CHIFFRAGE :
- Decomposer en 3 a 4 phases : cadrage (~15%), build (~60%), recette (~15%),
  documentation (~10%).
- Toujours proposer une phase de cadrage courte (0.5 a 1 j) pour valider le
  perimetre avant d'engager le reste.
- Si le client mentionne un budget, tu t'ajustes intelligemment : si le
  budget est trop bas pour ton TJM, tu proposes un perimetre reduit en Phase 1
  plutot qu'un refus.
- Tu donnes TOUJOURS une fourchette claire avec un prix cible, pas juste un
  TJM en l'air.

PLATEFORME CIBLE : {platform_name}
- Ton attendu : {tone}
- Longueur cible : environ {target_length_words} mots
- Formalite : {formality}
- Style du devis : {quote_style}
- A mettre en avant :
{emphasis}
- Structure recommandee :
{structure}

FORMAT DE SORTIE :
Tu rends UNIQUEMENT le texte de la reponse, pret a coller dans la plateforme.
Pas de meta-commentaire, pas de "voici ma proposition", pas de markdown lourd.
Tu peux utiliser des tirets simples (-) pour les listes, des titres courts en
majuscules, et des sauts de ligne. Les montants sont ecrits en clair
(ex : 3 200 EUR HT).

AVANT DE REPONDRE, analyse mentalement :
- Quel est le vrai besoin derriere la mission ?
- Le budget est-il coherent avec le perimetre ?
- Y a-t-il des zones d'ombre a eclaircir par des questions ?
- Quel livrable impressionnera le plus ce client ?
"""


def build_system_prompt(platform: str) -> str:
    """Construit le system prompt pour une plateforme donnee."""
    cfg = PLATFORM_CONFIG.get(platform, PLATFORM_CONFIG["other"])
    p = BAPTISTE_PROFILE
    return SYSTEM_PROMPT_TEMPLATE.format(
        language="francais" if cfg["language"] == "fr" else "english",
        full_name=p["full_name"],
        company=p["company"],
        email=p["email"],
        seniority_years=p["seniority_years"],
        languages=", ".join(p["languages"]),
        core_expertise="\n".join(f"  - {x}" for x in p["core_expertise"]),
        typical_deliverables="\n".join(f"  - {x}" for x in p["typical_deliverables"]),
        portfolio_highlight=p["portfolio_highlight"],
        tjm_base=PRICING["tjm_base"],
        tjm_expert=PRICING["tjm_expert"],
        tjm_senior=PRICING["tjm_senior"],
        forfait_discovery=PRICING["forfait_discovery"],
        buffer_pct_str=f"{int(PRICING['buffer_pct']*100)}%",
        platform_name=cfg["name"],
        tone=cfg["tone"],
        target_length_words=cfg["target_length_words"],
        formality=cfg["formality"],
        quote_style=cfg["quote_style"],
        emphasis="\n".join(f"  - {x}" for x in cfg["emphasis"]),
        structure="\n".join(f"  {i+1}. {x}" for i, x in enumerate(cfg["structure"])),
    )


def build_user_message(mission_text: str, budget_hint: str = "", urgency: str = "") -> str:
    """Construit le message user avec la mission et les hints."""
    parts = ["MISSION A TRAITER :", mission_text.strip()]
    if budget_hint:
        parts.append(f"\nBUDGET INDICATIF COMMUNIQUE : {budget_hint}")
    if urgency:
        parts.append(f"URGENCE : {urgency}")
    parts.append(
        "\nRedige la reponse complete, prete a coller dans la plateforme. "
        "Respecte strictement le ton, la longueur et la structure definis pour "
        "cette plateforme. Inclus un devis chiffre clair. Signe Baptiste Thevenot."
    )
    return "\n".join(parts)
