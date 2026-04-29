"""Livrables & Devis — generation automatique de documents commerciaux.

Genere des devis, propositions commerciales et livrables au format HTML/JSON
prets a etre convertis en PDF ou envoyes par email.
"""

import os
import json
import logging
from datetime import datetime, timedelta

log = logging.getLogger("commercial-agent")

# Directory for generated documents
LIVRABLES_DIR = os.path.join(os.path.dirname(__file__), "..", "livrables")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


# --- Templates de devis ---

DEVIS_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 2rem; }}
.header {{ display: flex; justify-content: space-between; border-bottom: 3px solid #2c7be5; padding-bottom: 1rem; margin-bottom: 2rem; }}
.header h1 {{ color: #1a2a3a; font-size: 1.5rem; }}
.header .company {{ text-align: right; color: #666; font-size: 0.85rem; }}
.info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem; }}
.info-box {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; }}
.info-box h3 {{ font-size: 0.8rem; text-transform: uppercase; color: #999; margin-bottom: 0.5rem; }}
table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
th {{ background: #1a2a3a; color: white; padding: 0.75rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; }}
td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #eee; }}
tr:hover {{ background: #f8f9fa; }}
.amount {{ text-align: right; font-variant-numeric: tabular-nums; }}
.total-row {{ font-weight: bold; background: #f0f4ff; }}
.total-row td {{ border-top: 2px solid #2c7be5; }}
.footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #eee; font-size: 0.8rem; color: #999; }}
.conditions {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1.5rem; font-size: 0.82rem; }}
.conditions h4 {{ margin-bottom: 0.5rem; color: #1a2a3a; }}
.validity {{ color: #2c7be5; font-weight: 600; }}
</style>
</head>
<body>
<div class="header">
    <div>
        <h1>DEVIS N&deg; {numero}</h1>
        <p>Date : {date}</p>
        <p class="validity">Valide jusqu'au : {date_validite}</p>
    </div>
    <div class="company">
        <strong>{company_name}</strong><br>
        {company_email}<br>
        {company_phone}
    </div>
</div>
<div class="info-grid">
    <div class="info-box">
        <h3>Emetteur</h3>
        <strong>{company_name}</strong><br>
        {company_email}
    </div>
    <div class="info-box">
        <h3>Client</h3>
        <strong>{client_name}</strong><br>
        {client_company}<br>
        {client_email}
    </div>
</div>
<h3>Objet : {objet}</h3>
<table>
    <thead>
        <tr>
            <th>Description</th>
            <th>Quantite</th>
            <th>Prix unitaire HT</th>
            <th class="amount">Total HT</th>
        </tr>
    </thead>
    <tbody>
        {lignes}
    </tbody>
    <tfoot>
        <tr class="total-row">
            <td colspan="3">Total HT</td>
            <td class="amount">{total_ht} &euro;</td>
        </tr>
        <tr class="total-row">
            <td colspan="3">TVA ({tva_rate}%)</td>
            <td class="amount">{total_tva} &euro;</td>
        </tr>
        <tr class="total-row" style="font-size: 1.1rem;">
            <td colspan="3">Total TTC</td>
            <td class="amount">{total_ttc} &euro;</td>
        </tr>
    </tfoot>
</table>
<div class="conditions">
    <h4>Conditions</h4>
    <ul>
        <li>Paiement : {conditions_paiement}</li>
        <li>Validite : 30 jours a compter de la date d'emission</li>
        <li>Delai de realisation : {delai}</li>
    </ul>
</div>
<div class="footer">
    <p>Document genere automatiquement par SNB Consulting — Agent Commercial IA</p>
</div>
</body>
</html>"""

PROPOSITION_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 2rem; }}
.cover {{ background: linear-gradient(135deg, #1a2a3a, #2c3e50); color: white; padding: 3rem; border-radius: 12px; margin-bottom: 2rem; }}
.cover h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
.cover p {{ opacity: 0.8; }}
.cover .meta {{ margin-top: 1.5rem; font-size: 0.85rem; opacity: 0.7; }}
section {{ margin: 2rem 0; }}
section h2 {{ color: #1a2a3a; border-bottom: 2px solid #2c7be5; padding-bottom: 0.5rem; margin-bottom: 1rem; }}
.highlight {{ background: #f0f4ff; border-left: 4px solid #2c7be5; padding: 1rem 1.5rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }}
.deliverables {{ list-style: none; padding: 0; }}
.deliverables li {{ padding: 0.75rem 1rem; border-bottom: 1px solid #eee; display: flex; align-items: flex-start; gap: 0.75rem; }}
.deliverables li::before {{ content: "✓"; color: #2c7be5; font-weight: bold; flex-shrink: 0; }}
.pricing {{ background: #f8f9fa; padding: 1.5rem; border-radius: 12px; }}
.pricing table {{ width: 100%; border-collapse: collapse; }}
.pricing th {{ text-align: left; padding: 0.5rem; color: #666; font-size: 0.8rem; text-transform: uppercase; }}
.pricing td {{ padding: 0.5rem; border-bottom: 1px solid #eee; }}
.pricing .total {{ font-weight: bold; font-size: 1.2rem; color: #1a2a3a; }}
.footer {{ margin-top: 3rem; text-align: center; color: #999; font-size: 0.8rem; }}
</style>
</head>
<body>
<div class="cover">
    <h1>{titre}</h1>
    <p>{sous_titre}</p>
    <div class="meta">
        Proposition pour <strong>{client_name}</strong> | {date} | Ref: {reference}
    </div>
</div>
<section>
    <h2>Contexte</h2>
    <p>{contexte}</p>
</section>
<section>
    <h2>Notre approche</h2>
    <p>{approche}</p>
</section>
<section>
    <h2>Livrables</h2>
    <ul class="deliverables">
        {livrables_html}
    </ul>
</section>
<section>
    <h2>Planning previsionnel</h2>
    {planning_html}
</section>
<section>
    <h2>Investissement</h2>
    <div class="pricing">
        <table>
            {pricing_html}
        </table>
    </div>
</section>
<section>
    <h2>Prochaines etapes</h2>
    <div class="highlight">
        <p>{prochaines_etapes}</p>
    </div>
</section>
<div class="footer">
    <p>SNB Consulting — Proposition commerciale confidentielle</p>
    <p>{company_name} | {company_email}</p>
</div>
</body>
</html>"""


# --- Tool definitions ---

LIVRABLES_TOOLS = [
    {
        "name": "livrables_create_devis",
        "description": "Generer un devis professionnel au format HTML. Le devis inclut les lignes de prestation, totaux HT/TTC, conditions de paiement et delais. Le fichier est sauve dans le dossier livrables/.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Nom du client"},
                "client_company": {"type": "string", "description": "Entreprise du client"},
                "client_email": {"type": "string", "description": "Email du client"},
                "objet": {"type": "string", "description": "Objet du devis (ex: 'Developpement application web')"},
                "lignes": {
                    "type": "array",
                    "description": "Lignes du devis",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "Description de la prestation"},
                            "quantite": {"type": "number", "description": "Quantite (jours, heures, unites)"},
                            "prix_unitaire": {"type": "number", "description": "Prix unitaire HT en euros"},
                        },
                        "required": ["description", "quantite", "prix_unitaire"],
                    },
                },
                "conditions_paiement": {
                    "type": "string",
                    "description": "Conditions de paiement (ex: '30 jours fin de mois', '50% a la commande')",
                    "default": "30 jours fin de mois",
                },
                "delai": {
                    "type": "string",
                    "description": "Delai de realisation (ex: '4 semaines', '2 mois')",
                    "default": "A definir",
                },
                "tva_rate": {
                    "type": "number",
                    "description": "Taux de TVA en pourcentage (defaut: 20)",
                    "default": 20,
                },
            },
            "required": ["client_name", "client_email", "objet", "lignes"],
        },
    },
    {
        "name": "livrables_create_proposition",
        "description": "Generer une proposition commerciale complete au format HTML. Inclut contexte, approche, livrables detailles, planning et pricing. Le fichier est sauve dans le dossier livrables/.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Nom du client ou de l'entreprise"},
                "titre": {"type": "string", "description": "Titre de la proposition (ex: 'Refonte du site e-commerce')"},
                "sous_titre": {"type": "string", "description": "Sous-titre ou accroche"},
                "contexte": {"type": "string", "description": "Description du contexte et des besoins du client"},
                "approche": {"type": "string", "description": "Description de l'approche proposee"},
                "livrables": {
                    "type": "array",
                    "description": "Liste des livrables avec description",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titre": {"type": "string", "description": "Nom du livrable"},
                            "description": {"type": "string", "description": "Description detaillee"},
                        },
                        "required": ["titre"],
                    },
                },
                "planning": {
                    "type": "array",
                    "description": "Phases du planning avec durees",
                    "items": {
                        "type": "object",
                        "properties": {
                            "phase": {"type": "string", "description": "Nom de la phase"},
                            "duree": {"type": "string", "description": "Duree estimee"},
                            "livrables": {"type": "string", "description": "Livrables de cette phase"},
                        },
                        "required": ["phase", "duree"],
                    },
                },
                "pricing": {
                    "type": "array",
                    "description": "Lignes de tarification",
                    "items": {
                        "type": "object",
                        "properties": {
                            "poste": {"type": "string", "description": "Poste de cout"},
                            "montant": {"type": "number", "description": "Montant HT en euros"},
                        },
                        "required": ["poste", "montant"],
                    },
                },
                "prochaines_etapes": {
                    "type": "string",
                    "description": "Description des prochaines etapes (ex: 'Un appel de cadrage de 30min pour valider les besoins...')",
                },
            },
            "required": ["client_name", "titre", "contexte", "livrables"],
        },
    },
    {
        "name": "livrables_list",
        "description": "Lister tous les livrables generes (devis et propositions). Retourne la liste des fichiers avec leurs metadonnees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type_filter": {
                    "type": "string",
                    "enum": ["all", "devis", "proposition"],
                    "description": "Filtrer par type de livrable (defaut: all)",
                },
            },
            "required": [],
        },
    },
]


# --- Tool Execution ---

def execute_livrables_tool(name: str, input_data: dict) -> str:
    """Execute a livrables tool and return the result as a string."""
    try:
        if name == "livrables_create_devis":
            return _create_devis(input_data)
        elif name == "livrables_create_proposition":
            return _create_proposition(input_data)
        elif name == "livrables_list":
            return _list_livrables(input_data)
        else:
            return f"Error: Unknown livrables tool '{name}'"
    except Exception as e:
        log.error(f"Livrables tool error: {e}")
        return f"Error executing {name}: {str(e)}"


def _create_devis(input_data: dict) -> str:
    """Generate a professional devis (quote) in HTML."""
    os.makedirs(LIVRABLES_DIR, exist_ok=True)

    now = datetime.now()
    numero = f"DEV-{now.strftime('%Y%m%d')}-{now.strftime('%H%M')}"
    date = now.strftime("%d/%m/%Y")
    date_validite = (now + timedelta(days=30)).strftime("%d/%m/%Y")

    company_name = os.getenv("AGENT_OWNER_NAME", "SNB Consulting")
    company_email = os.getenv("AGENT_OWNER_EMAIL", "contact@snb-consulting.com")

    # Build line items
    lignes_html = ""
    total_ht = 0
    for ligne in input_data["lignes"]:
        qty = ligne["quantite"]
        price = ligne["prix_unitaire"]
        line_total = qty * price
        total_ht += line_total
        lignes_html += f"""        <tr>
            <td>{ligne['description']}</td>
            <td>{qty}</td>
            <td class="amount">{price:,.2f} &euro;</td>
            <td class="amount">{line_total:,.2f} &euro;</td>
        </tr>\n"""

    tva_rate = input_data.get("tva_rate", 20)
    total_tva = total_ht * tva_rate / 100
    total_ttc = total_ht + total_tva

    html = DEVIS_TEMPLATE.format(
        numero=numero,
        date=date,
        date_validite=date_validite,
        company_name=company_name,
        company_email=company_email,
        company_phone="",
        client_name=input_data["client_name"],
        client_company=input_data.get("client_company", ""),
        client_email=input_data["client_email"],
        objet=input_data["objet"],
        lignes=lignes_html,
        total_ht=f"{total_ht:,.2f}",
        tva_rate=tva_rate,
        total_tva=f"{total_tva:,.2f}",
        total_ttc=f"{total_ttc:,.2f}",
        conditions_paiement=input_data.get("conditions_paiement", "30 jours fin de mois"),
        delai=input_data.get("delai", "A definir"),
    )

    filename = f"devis_{numero}.html"
    filepath = os.path.join(LIVRABLES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # Save metadata
    meta = {
        "type": "devis",
        "numero": numero,
        "date": date,
        "client": input_data["client_name"],
        "objet": input_data["objet"],
        "total_ht": total_ht,
        "total_ttc": total_ttc,
        "filename": filename,
        "created_at": now.isoformat(),
    }
    meta_path = os.path.join(LIVRABLES_DIR, f"devis_{numero}.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log.info(f"Devis {numero} cree: {filepath} ({total_ttc:.2f} EUR TTC)")

    return json.dumps({
        "status": "created",
        "type": "devis",
        "numero": numero,
        "filename": filename,
        "client": input_data["client_name"],
        "objet": input_data["objet"],
        "total_ht": f"{total_ht:,.2f} EUR",
        "total_ttc": f"{total_ttc:,.2f} EUR",
        "path": filepath,
    }, ensure_ascii=False)


def _create_proposition(input_data: dict) -> str:
    """Generate a commercial proposal in HTML."""
    os.makedirs(LIVRABLES_DIR, exist_ok=True)

    now = datetime.now()
    reference = f"PROP-{now.strftime('%Y%m%d')}-{now.strftime('%H%M')}"
    date = now.strftime("%d/%m/%Y")

    company_name = os.getenv("AGENT_OWNER_NAME", "SNB Consulting")
    company_email = os.getenv("AGENT_OWNER_EMAIL", "contact@snb-consulting.com")

    # Build livrables list
    livrables_html = ""
    for liv in input_data.get("livrables", []):
        desc = f" — {liv['description']}" if liv.get("description") else ""
        livrables_html += f"        <li><strong>{liv['titre']}</strong>{desc}</li>\n"

    # Build planning table
    planning_html = '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">'
    planning_html += '<tr><th style="text-align:left;padding:0.5rem;border-bottom:2px solid #2c7be5;">Phase</th>'
    planning_html += '<th style="text-align:left;padding:0.5rem;border-bottom:2px solid #2c7be5;">Duree</th>'
    planning_html += '<th style="text-align:left;padding:0.5rem;border-bottom:2px solid #2c7be5;">Livrables</th></tr>'
    for phase in input_data.get("planning", []):
        planning_html += f'<tr><td style="padding:0.5rem;border-bottom:1px solid #eee;">{phase["phase"]}</td>'
        planning_html += f'<td style="padding:0.5rem;border-bottom:1px solid #eee;">{phase["duree"]}</td>'
        planning_html += f'<td style="padding:0.5rem;border-bottom:1px solid #eee;">{phase.get("livrables", "")}</td></tr>'
    planning_html += '</table>'

    if not input_data.get("planning"):
        planning_html = '<p><em>Planning a definir lors du cadrage.</em></p>'

    # Build pricing table
    pricing_html = '<tr><th>Poste</th><th style="text-align:right;">Montant HT</th></tr>'
    total = 0
    for item in input_data.get("pricing", []):
        pricing_html += f'<tr><td>{item["poste"]}</td><td style="text-align:right;">{item["montant"]:,.2f} &euro;</td></tr>'
        total += item["montant"]
    if input_data.get("pricing"):
        pricing_html += f'<tr><td class="total" style="border-top:2px solid #2c7be5;padding-top:0.75rem;">Total HT</td>'
        pricing_html += f'<td class="total" style="text-align:right;border-top:2px solid #2c7be5;padding-top:0.75rem;">{total:,.2f} &euro;</td></tr>'
    else:
        pricing_html = '<tr><td colspan="2"><em>Tarification a definir apres cadrage.</em></td></tr>'

    html = PROPOSITION_TEMPLATE.format(
        titre=input_data["titre"],
        sous_titre=input_data.get("sous_titre", "Proposition commerciale"),
        client_name=input_data["client_name"],
        date=date,
        reference=reference,
        contexte=input_data["contexte"],
        approche=input_data.get("approche", "Notre approche sera definie lors du cadrage initial."),
        livrables_html=livrables_html,
        planning_html=planning_html,
        pricing_html=pricing_html,
        prochaines_etapes=input_data.get("prochaines_etapes",
            "Nous vous proposons un appel de cadrage de 30 minutes pour valider ensemble les besoins "
            "et affiner cette proposition. N'hesitez pas a nous contacter."),
        company_name=company_name,
        company_email=company_email,
    )

    filename = f"proposition_{reference}.html"
    filepath = os.path.join(LIVRABLES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # Save metadata
    meta = {
        "type": "proposition",
        "reference": reference,
        "date": date,
        "client": input_data["client_name"],
        "titre": input_data["titre"],
        "total_ht": total,
        "nb_livrables": len(input_data.get("livrables", [])),
        "filename": filename,
        "created_at": now.isoformat(),
    }
    meta_path = os.path.join(LIVRABLES_DIR, f"proposition_{reference}.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log.info(f"Proposition {reference} creee: {filepath}")

    return json.dumps({
        "status": "created",
        "type": "proposition",
        "reference": reference,
        "filename": filename,
        "client": input_data["client_name"],
        "titre": input_data["titre"],
        "total_ht": f"{total:,.2f} EUR" if total > 0 else "A definir",
        "nb_livrables": len(input_data.get("livrables", [])),
        "path": filepath,
    }, ensure_ascii=False)


def _list_livrables(input_data: dict) -> str:
    """List all generated livrables."""
    if not os.path.exists(LIVRABLES_DIR):
        return json.dumps({"total": 0, "livrables": []}, ensure_ascii=False)

    type_filter = input_data.get("type_filter", "all")
    livrables = []

    for filename in sorted(os.listdir(LIVRABLES_DIR), reverse=True):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(LIVRABLES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if type_filter != "all" and meta.get("type") != type_filter:
                continue
            livrables.append(meta)
        except (json.JSONDecodeError, IOError):
            continue

    return json.dumps({
        "total": len(livrables),
        "livrables": livrables,
    }, ensure_ascii=False)
