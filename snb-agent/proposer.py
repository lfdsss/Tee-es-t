"""SNB Mission Hunter — Generation de propositions structurees (packaging complet) via Claude API.
NE JAMAIS mentionner S&B Consulting dans les propositions.

Chaque proposition est un PACKAGING complet : analyse besoin, phases, livrables,
timeline, prix, resultat attendu — pour faciliter la decision du client.
"""

import json
import logging
import re
from typing import Optional, Dict, Any
import anthropic
from models import RawMission, Proposal
from profile import PROFILE

logger = logging.getLogger("snb.proposer")


PACKAGING_PROMPT_FR = """Tu es {name}, consultant freelance independant base a Toulouse.

PROFIL :
{bio}

COMPETENCES CLES : {skills}
TARIFS : TJM {tjm} EUR/jour HT — Forfait disponible
LANGUES : Francais natif, Anglais courant, Espagnol courant
DISPONIBILITE : Immediate, 100% remote ou hybride

MISSION CLIENT :
Titre : {title}
Source : {source}
Type detecte : {mission_type}
Description : {description}

INSTRUCTIONS :
Genere un PACKAGING complet de proposition au format JSON strict, structure pour faciliter la decision du client et generer un PowerPoint de 10 pages. Le packaging doit montrer une comprehension precise du besoin, une approche professionnelle, et un cadre clair (phases, livrables, prix, resultat).

Retourne UNIQUEMENT un objet JSON valide avec cette structure exacte :
{{
  "intro": "1-2 phrases d'accroche montrant que tu as compris le besoin reel du client",
  "executive_summary": "Resume executif de 2-3 phrases donnant une vue d'ensemble de la proposition, la valeur ajoutee et le resultat attendu",
  "comprehension": "Reformulation du besoin client en 2-3 phrases (ce que tu as compris de leur enjeu)",
  "approach": "Approche methodologique en 2-3 phrases (comment tu vas y aller)",
  "methodology": "Explication detaillee de la methodologie utilisee (agile, lean, iterative, etc.) en 3-4 phrases",
  "architecture": "Description de l'architecture technique ou organisationnelle proposee en 2-3 phrases",
  "tools_used": ["Outil/technologie 1", "Outil/technologie 2", "Outil/technologie 3"],
  "phases": [
    {{"name": "Phase 1 - Cadrage & analyse", "objective": "Objectif court de cette phase", "duration": "1 semaine", "tasks": ["tache 1", "tache 2"], "deliverable": "Livrable de cette phase", "tools": ["Outil 1", "Outil 2"]}},
    {{"name": "Phase 2 - Developpement", "objective": "Objectif court", "duration": "X semaines", "tasks": ["..."], "deliverable": "...", "tools": ["..."]}},
    {{"name": "Phase 3 - Livraison & accompagnement", "objective": "Objectif court", "duration": "...", "tasks": ["..."], "deliverable": "...", "tools": ["..."]}}
  ],
  "timeline": "Duree totale estimee",
  "deliverables": [
    {{"name": "Nom du livrable 1", "description": "Description detaillee", "format": "PDF"}},
    {{"name": "Nom du livrable 2", "description": "Description detaillee", "format": "Code"}},
    {{"name": "Nom du livrable 3", "description": "Description detaillee", "format": "Documentation"}}
  ],
  "expected_outcome": "Resultat optimal attendu pour le client en 1-2 phrases concretes",
  "kpis": ["KPI mesurable 1", "KPI mesurable 2", "KPI mesurable 3"],
  "guarantees": ["Garantie 1", "Garantie 2"],
  "pricing": {{
    "model": "forfait OU regie OU mixte",
    "amount": "Montant ou fourchette en EUR HT",
    "payment": "30% commande / 70% livraison ou autre",
    "detail": [
      {{"item": "Phase 1 - Cadrage", "days": 2, "amount": "900 EUR HT"}},
      {{"item": "Phase 2 - Developpement", "days": 10, "amount": "4500 EUR HT"}},
      {{"item": "Phase 3 - Livraison", "days": 3, "amount": "1350 EUR HT"}}
    ]
  }},
  "next_step": "Proposition concrete pour la suite (RDV de cadrage 30 min, demo, etc.)",
  "signature": "Baptiste Thevenot, Consultant Web & IA"
}}

REGLES STRICTES :
- JAMAIS mentionner "S&B Consulting" ni "S&B"
- Adapter le contenu au type de mission ({mission_type})
- Etre concret, pas de bla-bla, pas de jargon inutile
- Phases adaptees a la complexite reelle (pas forcement 3 phases — peut etre 2, 4 ou 5)
- Tarification realiste basee sur TJM 450 EUR/jour
- KPIs mesurables et concrets
- Garanties professionnelles realistes
- JSON strict valide, pas de texte avant/apres"""


PACKAGING_PROMPT_EN = """You are {name}, a freelance consultant based in Toulouse, France.

PROFILE:
{bio}

KEY SKILLS: {skills}
RATES: {tjm} EUR/day — Fixed-price available
LANGUAGES: French native, English fluent, Spanish fluent
AVAILABILITY: Immediate, 100% remote or hybrid

CLIENT MISSION:
Title: {title}
Source: {source}
Detected type: {mission_type}
Description: {description}

INSTRUCTIONS:
Generate a complete PROPOSAL PACKAGE in strict JSON format, structured to help the client make their decision and generate a 10-page PowerPoint. The package must show precise understanding of the need, a professional approach, and a clear framework (phases, deliverables, pricing, outcome).

Return ONLY a valid JSON object with this exact structure:
{{
  "intro": "1-2 hook sentences showing you understood the client's real need",
  "executive_summary": "2-3 sentence executive summary giving an overview of the proposal, value added and expected outcome",
  "comprehension": "Reformulation of the client's need in 2-3 sentences",
  "approach": "Methodological approach in 2-3 sentences",
  "methodology": "Detailed methodology explanation (agile, lean, iterative, etc.) in 3-4 sentences",
  "architecture": "Description of the proposed technical or organizational architecture in 2-3 sentences",
  "tools_used": ["Tool/technology 1", "Tool/technology 2", "Tool/technology 3"],
  "phases": [
    {{"name": "Phase 1 - Discovery & analysis", "objective": "Short objective for this phase", "duration": "1 week", "tasks": ["task 1", "task 2"], "deliverable": "Phase deliverable", "tools": ["Tool 1", "Tool 2"]}},
    {{"name": "Phase 2 - Development", "objective": "Short objective", "duration": "X weeks", "tasks": ["..."], "deliverable": "...", "tools": ["..."]}},
    {{"name": "Phase 3 - Delivery & support", "objective": "Short objective", "duration": "...", "tasks": ["..."], "deliverable": "...", "tools": ["..."]}}
  ],
  "timeline": "Total estimated duration",
  "deliverables": [
    {{"name": "Deliverable name 1", "description": "Detailed description", "format": "PDF"}},
    {{"name": "Deliverable name 2", "description": "Detailed description", "format": "Code"}},
    {{"name": "Deliverable name 3", "description": "Detailed description", "format": "Documentation"}}
  ],
  "expected_outcome": "Optimal outcome for the client in 1-2 concrete sentences",
  "kpis": ["Measurable KPI 1", "Measurable KPI 2", "Measurable KPI 3"],
  "guarantees": ["Guarantee 1", "Guarantee 2"],
  "pricing": {{
    "model": "fixed-price OR daily-rate OR mixed",
    "amount": "Amount or range in EUR",
    "payment": "30% upfront / 70% on delivery or other",
    "detail": [
      {{"item": "Phase 1 - Discovery", "days": 2, "amount": "900 EUR"}},
      {{"item": "Phase 2 - Development", "days": 10, "amount": "4500 EUR"}},
      {{"item": "Phase 3 - Delivery", "days": 3, "amount": "1350 EUR"}}
    ]
  }},
  "next_step": "Concrete next step proposal (30 min discovery call, demo, etc.)",
  "signature": "Baptiste Thevenot, Web & AI Consultant"
}}

STRICT RULES:
- NEVER mention "S&B Consulting" or "S&B"
- Adapt content to mission type ({mission_type})
- Be concrete, no fluff, no useless jargon
- Phases adapted to actual complexity (not necessarily 3 — could be 2, 4 or 5)
- Realistic pricing based on EUR 450/day rate
- KPIs must be measurable and concrete
- Professional and realistic guarantees
- Valid strict JSON, no text before/after"""


class Proposer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, mission: RawMission, mission_type: str = "other", **kwargs) -> Optional[Proposal]:
        """Generate a structured packaging proposal."""
        text_sample = f"{mission.title} {(mission.description or '')[:200]}"
        lang = self._detect_language(text_sample)

        prompt_template = PACKAGING_PROMPT_FR if lang == "fr" else PACKAGING_PROMPT_EN
        prompt = prompt_template.format(
            name=PROFILE["name"],
            bio=PROFILE["bio_full"],
            skills=", ".join(PROFILE["skills_primary"][:6]),
            tjm=PROFILE["tjm"],
            title=mission.title,
            description=(mission.description or "")[:2000],
            source=mission.source,
            mission_type=mission_type,
        )

        try:
            response = self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text.strip()
            raw_text = raw_text.replace("S&B Consulting", "").replace("S&B", "")

            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if not json_match:
                logger.error(f"No JSON found in response for {mission.title[:40]}")
                return None

            try:
                package = json.loads(json_match.group(0))
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {mission.title[:40]}: {e}")
                return None

            text = self._render_text(package, lang)

            return Proposal(
                mission_id="",
                text=text,
                language=lang,
                template_used=f"packaging_v3_{mission_type}",
                status="ready",
            )
        except Exception as e:
            logger.error(f"Erreur generation proposition: {e}")
            return None

    @staticmethod
    def _render_text(pkg: Dict[str, Any], lang: str) -> str:
        """Render the JSON package as a structured plain-text proposal."""
        lines = []
        lines.append(pkg.get("intro", ""))
        lines.append("")

        if pkg.get("executive_summary"):
            lines.append("RESUME EXECUTIF" if lang == "fr" else "EXECUTIVE SUMMARY")
            lines.append(pkg["executive_summary"])
            lines.append("")

        if pkg.get("comprehension"):
            lines.append("VOTRE BESOIN" if lang == "fr" else "YOUR NEED")
            lines.append(pkg["comprehension"])
            lines.append("")

        if pkg.get("approach"):
            lines.append("MON APPROCHE" if lang == "fr" else "MY APPROACH")
            lines.append(pkg["approach"])
            lines.append("")

        if pkg.get("methodology"):
            lines.append("METHODOLOGIE" if lang == "fr" else "METHODOLOGY")
            lines.append(pkg["methodology"])
            lines.append("")

        if pkg.get("architecture"):
            lines.append("ARCHITECTURE" if lang == "fr" else "ARCHITECTURE")
            lines.append(pkg["architecture"])
            lines.append("")

        if pkg.get("tools_used"):
            lines.append("OUTILS & TECHNOLOGIES" if lang == "fr" else "TOOLS & TECHNOLOGIES")
            for tool in pkg["tools_used"]:
                lines.append(f"  - {tool}")
            lines.append("")

        if pkg.get("phases"):
            lines.append("PHASES" if lang == "fr" else "PHASES")
            for i, p in enumerate(pkg["phases"], 1):
                lines.append(f"{p.get('name', f'Phase {i}')} — {p.get('duration', '')}")
                if p.get("objective"):
                    lines.append(f"  Objectif: {p['objective']}" if lang == "fr" else f"  Objective: {p['objective']}")
                for t in p.get("tasks", []):
                    lines.append(f"  - {t}")
                if p.get("deliverable"):
                    lines.append(f"  Livrable: {p['deliverable']}" if lang == "fr" else f"  Deliverable: {p['deliverable']}")
                if p.get("tools"):
                    tools_str = ", ".join(p["tools"])
                    lines.append(f"  Outils: {tools_str}" if lang == "fr" else f"  Tools: {tools_str}")
                lines.append("")

        if pkg.get("timeline"):
            lines.append(("DUREE TOTALE: " if lang == "fr" else "TOTAL DURATION: ") + pkg["timeline"])

        if pkg.get("deliverables"):
            lines.append("")
            lines.append("LIVRABLES FINAUX" if lang == "fr" else "FINAL DELIVERABLES")
            for d in pkg["deliverables"]:
                if isinstance(d, dict):
                    lines.append(f"  - {d.get('name', '')} ({d.get('format', '')}) : {d.get('description', '')}")
                else:
                    lines.append(f"  - {d}")

        if pkg.get("expected_outcome"):
            lines.append("")
            lines.append("RESULTAT ATTENDU" if lang == "fr" else "EXPECTED OUTCOME")
            lines.append(pkg["expected_outcome"])

        if pkg.get("kpis"):
            lines.append("")
            lines.append("INDICATEURS DE PERFORMANCE (KPIs)" if lang == "fr" else "KEY PERFORMANCE INDICATORS (KPIs)")
            for kpi in pkg["kpis"]:
                lines.append(f"  - {kpi}")

        if pkg.get("guarantees"):
            lines.append("")
            lines.append("GARANTIES" if lang == "fr" else "GUARANTEES")
            for g in pkg["guarantees"]:
                lines.append(f"  - {g}")

        if pkg.get("pricing"):
            lines.append("")
            lines.append("TARIFICATION" if lang == "fr" else "PRICING")
            pr = pkg["pricing"]
            lines.append(f"  Modele: {pr.get('model', '')}")
            lines.append(f"  Montant: {pr.get('amount', '')}")
            lines.append(f"  Paiement: {pr.get('payment', '')}")
            if pr.get("detail"):
                lines.append("")
                lines.append("  Detail:" if lang == "fr" else "  Breakdown:")
                for item in pr["detail"]:
                    lines.append(f"    - {item.get('item', '')}: {item.get('days', '')} jours — {item.get('amount', '')}")

        if pkg.get("next_step"):
            lines.append("")
            lines.append("PROCHAINE ETAPE" if lang == "fr" else "NEXT STEP")
            lines.append(pkg["next_step"])

        if pkg.get("signature"):
            lines.append("")
            lines.append(pkg["signature"])

        text = "\n".join(lines)
        text += f"\n\n<!--PACKAGE_JSON:{json.dumps(pkg, ensure_ascii=False)}-->"
        return text

    @staticmethod
    def _detect_language(text: str) -> str:
        text_lower = text.lower()
        fr = ["developpeur", "developpement", "recherche", "projet", "entreprise", "nous", "besoin", "freelance"]
        en = ["developer", "development", "looking", "project", "company", "need", "team", "freelance"]
        fc = sum(1 for m in fr if m in text_lower)
        ec = sum(1 for m in en if m in text_lower)
        return "en" if ec > fc else "fr"
