"""SNB Mission Hunter — FastAPI endpoints.
P0 FIX: Health reads from Supabase agent_status table (shared between processes).
"""

import io
import json
import re
import time
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from profile import PROFILE
from document_generator import PDFGenerator, PPTXGenerator

logger = logging.getLogger("snb.api")

app = FastAPI(title="SNB Mission Hunter", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_started_at = time.time()
_db = None
_anthropic_client = None


def set_db(db):
    global _db
    _db = db


@app.on_event("startup")
async def startup():
    global _db, _anthropic_client
    if _db is None:
        try:
            from config import Config
            from db import Database
            config = Config.from_env()
            _db = Database(config.supabase_url, config.supabase_service_key)
            if config.anthropic_api_key:
                import anthropic
                _anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            logger.info("API DB initialized")
        except Exception as e:
            logger.warning(f"API DB init failed: {e}")


def _extract_package_json(proposal_text: str) -> dict:
    match = re.search(r'<!--PACKAGE_JSON:(.*?)-->', proposal_text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    json_match = re.search(r'\{.*\}', proposal_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


@app.get("/health")
async def health():
    uptime = int(time.time() - _started_at)
    h, r = divmod(uptime, 3600)
    m, s = divmod(r, 60)

    result = {
        "status": "running",
        "uptime": f"{h}h {m}m {s}s",
        "last_scan": None,
        "scans_total": 0,
        "missions_today": 0,
        "proposals_today": 0,
        "sources": {},
    }

    if not _db:
        return result

    try:
        today = datetime.now(timezone.utc).date().isoformat()

        agent_status = _db.get_agent_status()
        if agent_status:
            result["last_scan"] = agent_status.get("last_scan_at")
            result["scans_total"] = agent_status.get("scans_total", 0)

        logs = _db.client.table("scan_logs") \
            .select("source,status,started_at,missions_found,missions_new") \
            .gte("started_at", today) \
            .order("started_at", desc=True) \
            .limit(50) \
            .execute()

        scan_data = logs.data or []
        if not agent_status:
            result["scans_total"] = len(scan_data)
            if scan_data:
                result["last_scan"] = scan_data[0].get("started_at")

        sources = {}
        for s in scan_data:
            src = s.get("source", "?")
            if src not in sources:
                sources[src] = {
                    "last_scan": s.get("started_at"),
                    "status": s.get("status", "ok"),
                    "missions_found": s.get("missions_found", 0),
                }
        result["sources"] = sources

        missions_today = _db.client.table("missions") \
            .select("id", count="exact") \
            .gte("found_at", today) \
            .execute()
        result["missions_today"] = missions_today.count or 0

        proposals_today = _db.client.table("proposals") \
            .select("id", count="exact") \
            .gte("created_at", today) \
            .execute()
        result["proposals_today"] = proposals_today.count or 0

    except Exception as e:
        logger.debug(f"Health DB read error: {e}")

    return result


@app.get("/stats")
async def stats():
    return await health()


@app.get("/debug")
async def debug():
    """Diagnostic endpoint — shows what's configured and what's broken."""
    import os
    checks = {
        "anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "anthropic_client_loaded": _anthropic_client is not None,
        "supabase_url": bool(os.getenv("SUPABASE_URL")),
        "supabase_key": bool(os.getenv("SUPABASE_SERVICE_KEY")),
        "db_connected": _db is not None,
        "smtp_user": bool(os.getenv("SMTP_USER")),
        "smtp_password": bool(os.getenv("SMTP_PASSWORD")),
        "telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
        "telegram_chat_id": bool(os.getenv("TELEGRAM_CHAT_ID")),
    }

    source_status = {}
    if _db:
        try:
            logs = _db.client.table("scan_logs") \
                .select("source,status,started_at,error_message") \
                .order("started_at", desc=True) \
                .limit(100) \
                .execute()
            for log in (logs.data or []):
                src = log.get("source", "?")
                if src not in source_status:
                    source_status[src] = {
                        "last_status": log.get("status"),
                        "last_scan": log.get("started_at"),
                        "last_error": log.get("error_message"),
                    }
        except Exception as e:
            source_status["_error"] = str(e)

    return {
        "checks": checks,
        "sources": source_status,
        "chat_ready": _anthropic_client is not None,
        "fix_instructions": {
            "chat": "Set ANTHROPIC_API_KEY in Railway env vars" if not _anthropic_client else "OK",
            "db": "Set SUPABASE_URL and SUPABASE_SERVICE_KEY" if not _db else "OK",
        },
    }


@app.get("/missions")
async def get_missions(limit: int = 50):
    if not _db:
        return {"error": "DB not init", "missions": []}
    try:
        missions = _db.get_recent_missions(limit=min(limit, 100))
        return {"missions": missions, "count": len(missions)}
    except Exception as e:
        return {"error": str(e), "missions": []}


@app.get("/devis/{mission_id}")
async def generate_devis(mission_id: str):
    """Generate a printable HTML invoice for a mission."""
    if not _db:
        return {"error": "DB not init"}
    try:
        mission = _db.client.table("missions").select("*").eq("id", mission_id).single().execute()
        m = mission.data
        if not m:
            return {"error": "Mission not found"}

        title = m.get("title", "Mission")
        company = m.get("company", "")
        budget = m.get("budget_raw", "")
        today_str = datetime.now().strftime("%d/%m/%Y")

        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Devis — {title}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Helvetica,sans-serif;color:#111;padding:40px;max-width:700px;margin:0 auto;font-size:14px;line-height:1.6}}
h1{{font-size:22px;margin-bottom:4px}}h2{{font-size:16px;border-bottom:1px solid #ddd;padding-bottom:4px;margin:20px 0 10px}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}td,th{{padding:8px 10px;border:1px solid #ddd;text-align:left}}th{{background:#f5f5f5}}
.footer{{margin-top:40px;font-size:11px;color:#888;text-align:center}}
@media print{{body{{padding:20px}}}}</style></head><body>
<div style="display:flex;justify-content:space-between;border-bottom:3px solid #111;padding-bottom:14px;margin-bottom:20px">
<div><h1>Baptiste Thevenot</h1><p style="color:#555;font-size:13px">Consultant Web & IA — Freelance</p>
<p style="font-size:12px;color:#888;margin-top:6px">10 chemin de Catala, 31100 Toulouse<br>bp.thevenot@gmail.com — 06 86 50 43 79<br>SIRET : 849 022 058</p></div>
<div style="text-align:right"><p style="font-size:18px;font-weight:bold">DEVIS</p><p style="font-size:12px;color:#888">{today_str}<br>Valable 30 jours</p></div></div>
<div style="background:#f5f7fa;border-radius:8px;padding:14px;margin-bottom:20px">
<p style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;font-weight:bold">Mission Freelance</p>
<p style="font-size:17px;font-weight:bold;margin-top:4px">{title}</p>
<p style="font-size:13px;color:#555">{company} — Remote — {budget}</p></div>
<h2>Tarification</h2>
<table><tr style="background:#f9f9f9"><td style="font-weight:bold">Taux horaire</td><td style="text-align:center;font-weight:bold;font-size:15px">60 EUR HT/h</td></tr>
<tr><td style="font-weight:bold">Taux journalier (TJM)</td><td style="text-align:center;font-weight:bold;font-size:15px">450 EUR HT/jour</td></tr>
<tr style="background:#f0fff4"><td style="font-weight:bold">Forfait mensuel</td><td style="text-align:center;font-weight:bold;font-size:17px">9 000 EUR HT/mois</td></tr></table>
<h2>Conditions</h2>
<p><strong>Disponibilite :</strong> Immediate<br><strong>Mode :</strong> 100% teletravail<br><strong>Paiement :</strong> 30% commande — 70% livraison<br>
<strong>Competences :</strong> React.js, Node.js, Shopify, Claude API, Python, Figma<br><strong>TVA :</strong> Non applicable — art. 293B du CGI</p>
<div style="margin-top:30px;border-top:1px solid #ddd;padding-top:14px;display:flex;justify-content:space-between">
<div><p style="font-size:12px;color:#888">Bon pour accord</p><div style="margin-top:20px;border-bottom:1px solid #ccc;width:160px"></div></div>
<div style="text-align:right;font-size:12px;color:#888">Baptiste Thevenot<br>Consultant Web & IA</div></div>
<p class="footer">Baptiste Thevenot — SIRET 849 022 058 — TVA non applicable art. 293B du CGI</p>
</body></html>"""
        return HTMLResponse(content=html)
    except Exception as e:
        return {"error": str(e)}


@app.get("/proposal/{proposal_id}/pdf")
async def download_pdf(proposal_id: str):
    """Generate and return PDF for a proposal."""
    if not _db:
        return {"error": "DB not init"}
    try:
        proposal = _db.client.table("proposals").select("*").eq("id", proposal_id).single().execute()
        if not proposal.data:
            return {"error": "Proposal not found"}

        proposal_data = proposal.data
        package_json = _extract_package_json(proposal_data.get("text", ""))
        if not package_json:
            return {"error": "No package data found in proposal"}

        mission_id = proposal_data.get("mission_id", "")
        mission_data = {}
        if mission_id:
            mission = _db.client.table("missions").select("*").eq("id", mission_id).single().execute()
            if mission.data:
                mission_data = mission.data

        generator = PDFGenerator()
        pdf_bytes = generator.generate(package_json, mission_data)

        safe_title = re.sub(r'[^\w\s-]', '', mission_data.get("title", "proposition"))[:50].strip()
        filename = f"Proposition_{safe_title}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return {"error": str(e)}


@app.get("/proposal/{proposal_id}/pptx")
async def download_pptx(proposal_id: str):
    """Generate and return PPTX for a proposal."""
    if not _db:
        return {"error": "DB not init"}
    try:
        proposal = _db.client.table("proposals").select("*").eq("id", proposal_id).single().execute()
        if not proposal.data:
            return {"error": "Proposal not found"}

        proposal_data = proposal.data
        package_json = _extract_package_json(proposal_data.get("text", ""))
        if not package_json:
            return {"error": "No package data found in proposal"}

        mission_id = proposal_data.get("mission_id", "")
        mission_data = {}
        if mission_id:
            mission = _db.client.table("missions").select("*").eq("id", mission_id).single().execute()
            if mission.data:
                mission_data = mission.data

        generator = PPTXGenerator()
        pptx_bytes = generator.generate(package_json, mission_data)

        safe_title = re.sub(r'[^\w\s-]', '', mission_data.get("title", "proposition"))[:50].strip()
        filename = f"Proposition_{safe_title}.pptx"

        return StreamingResponse(
            io.BytesIO(pptx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error(f"PPTX generation error: {e}")
        return {"error": str(e)}


@app.post("/chat")
async def chat(request: Request):
    """AI chatbot endpoint using Claude Opus 4.7."""
    try:
        body = await request.json()
        user_message = body.get("message", "")
        history = body.get("history", [])

        if not user_message:
            return {"error": "Empty message"}

        if not _anthropic_client:
            return {"response": f"Bonjour, je suis Baptiste Thevenot, consultant Web & IA freelance basé à Toulouse. Mon assistant IA est temporairement indisponible (clé API non configurée), mais vous pouvez me contacter directement : bp.thevenot@gmail.com ou 06 86 50 43 79."}

        p = PROFILE
        skills_primary = ", ".join(p.get("skills_primary", []))
        skills_secondary = ", ".join(p.get("skills_secondary", []))

        system_prompt = f"""Tu es {p['name']}, consultant freelance independant {p['title']} base a {p['location']}.

PROFIL COMPLET :
{p['bio_full']}

FORMATION : {p.get('education', '')}
EXPERIENCE : {p.get('experience_years', 5)} ans d'experience

COMPETENCES PRINCIPALES : {skills_primary}
COMPETENCES SECONDAIRES : {skills_secondary}

TARIFS : TJM {p['tjm']} EUR/jour HT | Taux horaire 60 EUR/h HT
LANGUES : {', '.join(p.get('languages', []))}
DISPONIBILITE : Immediate, 100% remote ou hybride

PORTFOLIO :
- La Francaise des Sauces — marque alimentaire premium, site Shopify complet, branding A-Z
- Chef IA — configurateur recettes interactif 3D avec IA
- Systeme multi-agents IA — 6 agents specialises, Claude API + Shopify MCP
- Audit cybersecurite — audit 936 comptes, migration Bitwarden

CONTACT :
- Email : {p.get('email', '')}
- Telephone : {p.get('phone', '')}
- Malt : {p.get('malt_url', '')}
- Codeur.com : {p.get('codeur_url', '')}
- LinkedIn : {p.get('linkedin_url', '')}

INSTRUCTIONS :
Tu reponds aux questions de maniere professionnelle, directe et chaleureuse.
Tu peux discuter de tes competences, ta disponibilite, tes tarifs (TJM {p['tjm']} EUR/jour), tes projets passes.
Tu es enthousiaste pour les nouvelles missions et tu proposes toujours une prochaine etape concrete.
JAMAIS mentionner "S&B Consulting" ni "S&B".
Reponds en francais par defaut, sauf si le message est en anglais."""

        messages = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        response = _anthropic_client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
        )

        reply = response.content[0].text.strip()
        reply = reply.replace("S&B Consulting", "").replace("S&B", "")

        return {"response": reply}

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"error": str(e)}
