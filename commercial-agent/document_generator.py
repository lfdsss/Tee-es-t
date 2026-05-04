#!/usr/bin/env python3
"""
Generateur de documents professionnels : devis, plan projet, facture.

Genere des documents HTML imprimables (A4) a partir des reponses de mission
stockees dans docs/missions/*.md ou a partir de donnees structurees.

Usage :
    python document_generator.py --mission docs/missions/xxx.md --type devis
    python document_generator.py --mission docs/missions/xxx.md --type all
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DOCS_DIR = Path("docs/documents")
MISSIONS_DIR = Path("docs/missions")
INDEX_FILE = DOCS_DIR / "index.json"

COMPANY = {
    "name": "SNB Consulting",
    "owner": "Baptiste Thevenot",
    "email": "bp.thevenot@gmail.com",
    "address": "France",
    "siret": "A renseigner",
    "tva": "Franchise en base de TVA - Art. 293 B du CGI",
    "status": "Entrepreneur Individuel",
}


def parse_mission_md(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = {}
    in_front = False
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---" and not in_front:
            in_front = True
            continue
        if line.strip() == "---" and in_front:
            body_start = i + 1
            break
        if in_front and ":" in line:
            key, val = line.split(":", 1)
            val = val.strip().strip('"')
            meta[key.strip()] = val

    body = "\n".join(lines[body_start:])
    mission_match = re.search(r"```\n(.*?)\n```", body, re.DOTALL)
    mission_text = mission_match.group(1).strip() if mission_match else ""

    response_match = re.search(r"## Reponse generee\s*\n(.*)", body, re.DOTALL)
    response_text = response_match.group(1).strip() if response_match else ""

    return {
        "meta": meta,
        "mission_text": mission_text,
        "response_text": response_text,
    }


def extract_phases(response: str) -> list[dict]:
    phases = []
    pattern = re.compile(
        r"Phase\s+(\d+)\s*[-:]\s*(.*?)\s*[-:]\s*([\d.,]+)\s*jours?\s*[-:]\s*([\d\s.,]+)\s*EUR",
        re.IGNORECASE,
    )
    for m in pattern.finditer(response):
        phases.append({
            "num": int(m.group(1)),
            "name": m.group(2).strip(),
            "days": float(m.group(3).replace(",", ".")),
            "price": float(re.sub(r"[^\d.]", "", m.group(4).replace(",", ".").replace(" ", ""))),
        })

    if not phases:
        line_pattern = re.compile(
            r"Phase\s+(\d+)\s*[-:]\s*(.*?)[-:]\s*([\d.,]+)\s*jour",
            re.IGNORECASE,
        )
        price_pattern = re.compile(r"([\d\s]+)\s*EUR", re.IGNORECASE)
        for m in line_pattern.finditer(response):
            num = int(m.group(1))
            name = m.group(2).strip()
            days = float(m.group(3).replace(",", "."))
            price_search = price_pattern.search(response[m.end():m.end() + 100])
            price = float(re.sub(r"\s", "", price_search.group(1))) if price_search else days * 550
            phases.append({"num": num, "name": name, "days": days, "price": price})

    if not phases:
        budget_match = re.search(r"([\d\s]+)\s*EUR\s*HT", response)
        total = float(re.sub(r"\s", "", budget_match.group(1))) if budget_match else 1500
        phases = [
            {"num": 1, "name": "Cadrage et validation du perimetre", "days": 0.5, "price": round(total * 0.15)},
            {"num": 2, "name": "Developpement et implementation", "days": 2, "price": round(total * 0.60)},
            {"num": 3, "name": "Tests et recette", "days": 1, "price": round(total * 0.15)},
            {"num": 4, "name": "Documentation et transfert", "days": 0.5, "price": round(total * 0.10)},
        ]

    return phases


def extract_total(phases: list[dict]) -> float:
    return sum(p["price"] for p in phases)


def extract_tjm(response: str) -> float:
    m = re.search(r"TJM\s*:?\s*([\d\s]+)\s*EUR", response, re.IGNORECASE)
    if m:
        return float(re.sub(r"\s", "", m.group(1)))
    return 550.0


def devis_number(mission_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    short = re.sub(r"[^a-zA-Z0-9]", "", mission_id)[:8].upper()
    return f"DEV-{ts}-{short}"


def facture_number(mission_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    short = re.sub(r"[^a-zA-Z0-9]", "", mission_id)[:8].upper()
    return f"FAC-{ts}-{short}"


CSS_PRINT = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; font-size: 13px; color: #1e293b; padding: 40px; max-width: 800px; margin: 0 auto; }
@media print { body { padding: 20px; } .no-print { display: none; } @page { margin: 1.5cm; } }
.header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 24px; border-bottom: 3px solid #0ea5e9; margin-bottom: 24px; }
.header-left h1 { font-size: 22px; font-weight: 800; color: #0f172a; }
.header-left p { font-size: 11px; color: #64748b; margin-top: 2px; }
.header-right { text-align: right; font-size: 11px; color: #64748b; line-height: 1.6; }
.doc-title { text-align: center; margin: 24px 0; }
.doc-title h2 { font-size: 18px; font-weight: 700; color: #0f172a; }
.doc-title .doc-num { font-size: 12px; color: #0ea5e9; font-weight: 600; margin-top: 4px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
.info-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
.info-box h3 { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0ea5e9; margin-bottom: 8px; }
.info-box p { font-size: 12px; line-height: 1.6; color: #334155; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; }
th { background: #0f172a; color: white; padding: 10px 12px; font-size: 11px; font-weight: 600; text-align: left; text-transform: uppercase; letter-spacing: 0.3px; }
td { padding: 10px 12px; font-size: 12px; border-bottom: 1px solid #e2e8f0; }
tr:nth-child(even) { background: #f8fafc; }
.total-row td { font-weight: 700; font-size: 14px; border-top: 2px solid #0f172a; background: white; }
.section { margin: 24px 0; }
.section h3 { font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
.section p, .section li { font-size: 12px; line-height: 1.7; color: #475569; }
.section ul { padding-left: 20px; }
.footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #94a3b8; text-align: center; }
.signature-block { margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.sig-box { border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; min-height: 100px; }
.sig-box h4 { font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 40px; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: 700; }
.badge-devis { background: #dbeafe; color: #1d4ed8; }
.badge-facture { background: #dcfce7; color: #166534; }
.badge-plan { background: #fef3c7; color: #92400e; }
.timeline { position: relative; padding-left: 24px; }
.timeline::before { content: ''; position: absolute; left: 8px; top: 0; bottom: 0; width: 2px; background: #0ea5e9; }
.timeline-item { position: relative; margin-bottom: 20px; }
.timeline-item::before { content: ''; position: absolute; left: -20px; top: 4px; width: 12px; height: 12px; border-radius: 50%; background: #0ea5e9; border: 2px solid white; box-shadow: 0 0 0 2px #0ea5e9; }
.timeline-item h4 { font-size: 13px; font-weight: 600; color: #0f172a; }
.timeline-item p { font-size: 11px; color: #64748b; margin-top: 2px; }
.btn-print { display: inline-block; padding: 10px 24px; background: #0ea5e9; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; margin: 8px 4px; }
.btn-print:hover { background: #0284c7; }
"""


def generate_devis(data: dict) -> str:
    meta = data["meta"]
    response = data["response_text"]
    phases = extract_phases(response)
    total = extract_total(phases)
    mission_id = meta.get("id", "unknown")
    num = devis_number(mission_id)
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    valid_until = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%d/%m/%Y")
    title = meta.get("title", "Mission")
    platform = meta.get("platform", "")
    budget = meta.get("budget_hint", "")

    rows = ""
    total_days = 0
    for p in phases:
        rows += f"""<tr>
            <td>Phase {p['num']}</td>
            <td>{p['name']}</td>
            <td style="text-align:center">{p['days']}</td>
            <td style="text-align:right">{p['price']:,.0f} EUR</td>
        </tr>\n"""
        total_days += p["days"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Devis {num} | SNB Consulting</title>
<style>{CSS_PRINT}</style>
</head>
<body>
<div class="no-print" style="text-align:center;margin-bottom:20px">
    <button class="btn-print" onclick="window.print()">Imprimer / PDF</button>
    <a class="btn-print" href="/documents.html" style="text-decoration:none">Retour</a>
</div>

<div class="header">
    <div class="header-left">
        <h1>SNB Consulting</h1>
        <p>{COMPANY['owner']} - {COMPANY['status']}</p>
        <p>{COMPANY['email']}</p>
    </div>
    <div class="header-right">
        <strong>DEVIS</strong><br>
        N. {num}<br>
        Date : {today}<br>
        Validite : {valid_until}
    </div>
</div>

<div class="doc-title">
    <span class="badge badge-devis">DEVIS</span>
    <h2>{title}</h2>
    <div class="doc-num">Reference : {num} | Plateforme : {platform}</div>
</div>

<div class="info-grid">
    <div class="info-box">
        <h3>Prestataire</h3>
        <p><strong>{COMPANY['owner']}</strong><br>
        {COMPANY['name']}<br>
        {COMPANY['email']}<br>
        {COMPANY['address']}<br>
        {COMPANY['status']}</p>
    </div>
    <div class="info-box">
        <h3>Client</h3>
        <p><strong>A completer</strong><br>
        Societe :<br>
        Adresse :<br>
        Contact :<br>
        Budget indicatif : {budget}</p>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th style="width:80px">Phase</th>
            <th>Description</th>
            <th style="width:80px;text-align:center">Jours</th>
            <th style="width:120px;text-align:right">Montant HT</th>
        </tr>
    </thead>
    <tbody>
        {rows}
        <tr class="total-row">
            <td colspan="2" style="text-align:right">TOTAL HT</td>
            <td style="text-align:center">{total_days}</td>
            <td style="text-align:right">{total:,.0f} EUR</td>
        </tr>
    </tbody>
</table>

<div class="section">
    <h3>Conditions</h3>
    <ul>
        <li>{COMPANY['tva']}</li>
        <li>Paiement : 30 jours date de facture</li>
        <li>Acompte de 30% a la commande</li>
        <li>Devis valable 30 jours</li>
        <li>Facturation a la phase, sur validation du livrable</li>
    </ul>
</div>

<div class="signature-block">
    <div class="sig-box">
        <h4>Le prestataire</h4>
        <p style="font-size:11px;color:#64748b">{COMPANY['owner']}<br>SNB Consulting</p>
    </div>
    <div class="sig-box">
        <h4>Le client (bon pour accord)</h4>
        <p style="font-size:11px;color:#64748b">Date et signature</p>
    </div>
</div>

<div class="footer">
    {COMPANY['name']} - {COMPANY['owner']} - {COMPANY['status']} | {COMPANY['email']}
</div>
</body>
</html>"""


def generate_plan_projet(data: dict) -> str:
    meta = data["meta"]
    response = data["response_text"]
    phases = extract_phases(response)
    total_days = sum(p["days"] for p in phases)
    title = meta.get("title", "Mission")
    urgency = meta.get("urgency", "")
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    timeline_items = ""
    cumul = 0
    for p in phases:
        start = cumul
        cumul += p["days"]
        timeline_items += f"""<div class="timeline-item">
            <h4>Phase {p['num']} : {p['name']}</h4>
            <p>Duree : {p['days']} jour(s) | Jour {start:.0f} a {cumul:.0f}</p>
        </div>\n"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Plan Projet - {title} | SNB Consulting</title>
<style>{CSS_PRINT}</style>
</head>
<body>
<div class="no-print" style="text-align:center;margin-bottom:20px">
    <button class="btn-print" onclick="window.print()">Imprimer / PDF</button>
    <a class="btn-print" href="/documents.html" style="text-decoration:none">Retour</a>
</div>

<div class="header">
    <div class="header-left">
        <h1>SNB Consulting</h1>
        <p>Plan de projet</p>
    </div>
    <div class="header-right">
        Date : {today}<br>
        Responsable : {COMPANY['owner']}
    </div>
</div>

<div class="doc-title">
    <span class="badge badge-plan">PLAN PROJET</span>
    <h2>{title}</h2>
    <div class="doc-num">Duree estimee : {total_days} jour(s) | {urgency}</div>
</div>

<div class="info-grid">
    <div class="info-box">
        <h3>Objectif</h3>
        <p>{data['mission_text'][:300]}{'...' if len(data['mission_text']) > 300 else ''}</p>
    </div>
    <div class="info-box">
        <h3>Perimetre</h3>
        <p><strong>Phases :</strong> {len(phases)}<br>
        <strong>Duree totale :</strong> {total_days} jour(s)<br>
        <strong>Livrables :</strong> 1 par phase<br>
        <strong>Validation :</strong> A chaque fin de phase</p>
    </div>
</div>

<div class="section">
    <h3>Planning previsionnel</h3>
    <div class="timeline">
        {timeline_items}
    </div>
</div>

<div class="section">
    <h3>Methodologie</h3>
    <ul>
        <li>Travail en phases courtes avec livrable concret par phase</li>
        <li>Validation client obligatoire avant passage a la phase suivante</li>
        <li>Point de synchronisation hebdomadaire (30 min)</li>
        <li>Echange asynchrone quotidien (Slack ou email)</li>
        <li>Remontee immediate des blocages</li>
        <li>Documentation continue integree a chaque phase</li>
    </ul>
</div>

<div class="section">
    <h3>Criteres de succes</h3>
    <ul>
        <li>Livrable fonctionnel a chaque fin de phase</li>
        <li>Tests valides par le client</li>
        <li>Documentation operationnelle a jour</li>
        <li>Respect du planning a +/- 20%</li>
    </ul>
</div>

<div class="section">
    <h3>Risques identifies</h3>
    <ul>
        <li>Acces aux systemes client (mitigation : cadrage Phase 1)</li>
        <li>Evolution du perimetre (mitigation : validation par phase)</li>
        <li>Disponibilite des interlocuteurs (mitigation : planning partage)</li>
    </ul>
</div>

<div class="footer">
    {COMPANY['name']} - {COMPANY['owner']} | {COMPANY['email']} | {today}
</div>
</body>
</html>"""


def generate_facture(data: dict) -> str:
    meta = data["meta"]
    response = data["response_text"]
    phases = extract_phases(response)
    total = extract_total(phases)
    mission_id = meta.get("id", "unknown")
    num = facture_number(mission_id)
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    due = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%d/%m/%Y")
    title = meta.get("title", "Mission")

    rows = ""
    total_days = 0
    for p in phases:
        rows += f"""<tr>
            <td>Phase {p['num']} - {p['name']}</td>
            <td style="text-align:center">{p['days']}</td>
            <td style="text-align:right">{p['price']:,.0f} EUR</td>
        </tr>\n"""
        total_days += p["days"]

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Facture {num} | SNB Consulting</title>
<style>{CSS_PRINT}</style>
</head>
<body>
<div class="no-print" style="text-align:center;margin-bottom:20px">
    <button class="btn-print" onclick="window.print()">Imprimer / PDF</button>
    <a class="btn-print" href="/documents.html" style="text-decoration:none">Retour</a>
</div>

<div class="header">
    <div class="header-left">
        <h1>SNB Consulting</h1>
        <p>{COMPANY['owner']} - {COMPANY['status']}</p>
        <p>{COMPANY['email']}</p>
    </div>
    <div class="header-right">
        <strong>FACTURE</strong><br>
        N. {num}<br>
        Date : {today}<br>
        Echeance : {due}
    </div>
</div>

<div class="doc-title">
    <span class="badge badge-facture">FACTURE</span>
    <h2>{title}</h2>
    <div class="doc-num">Reference : {num}</div>
</div>

<div class="info-grid">
    <div class="info-box">
        <h3>Emetteur</h3>
        <p><strong>{COMPANY['owner']}</strong><br>
        {COMPANY['name']}<br>
        {COMPANY['email']}<br>
        {COMPANY['status']}<br>
        SIRET : {COMPANY['siret']}</p>
    </div>
    <div class="info-box">
        <h3>Destinataire</h3>
        <p><strong>A completer</strong><br>
        Societe :<br>
        Adresse :<br>
        SIRET :</p>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th>Designation</th>
            <th style="width:80px;text-align:center">Quantite (j)</th>
            <th style="width:120px;text-align:right">Montant HT</th>
        </tr>
    </thead>
    <tbody>
        {rows}
    </tbody>
</table>

<table style="width:300px;margin-left:auto">
    <tr><td>Total HT</td><td style="text-align:right;font-weight:600">{total:,.0f} EUR</td></tr>
    <tr><td>TVA</td><td style="text-align:right;font-size:11px">Non applicable</td></tr>
    <tr class="total-row"><td>Total TTC</td><td style="text-align:right">{total:,.0f} EUR</td></tr>
</table>

<div class="section">
    <h3>Conditions de paiement</h3>
    <ul>
        <li>{COMPANY['tva']}</li>
        <li>Paiement par virement bancaire sous 30 jours</li>
        <li>En cas de retard : penalites de 3x le taux d'interet legal</li>
        <li>Indemnite forfaitaire de recouvrement : 40 EUR</li>
    </ul>
</div>

<div class="section">
    <h3>Coordonnees bancaires</h3>
    <p>IBAN : A renseigner<br>
    BIC : A renseigner<br>
    Banque : A renseigner</p>
</div>

<div class="footer">
    {COMPANY['name']} - {COMPANY['owner']} - {COMPANY['status']} | SIRET : {COMPANY['siret']} | {COMPANY['email']}
</div>
</body>
</html>"""


def generate_all(mission_path: Path, doc_types: list[str] | None = None) -> list[dict]:
    if doc_types is None:
        doc_types = ["devis", "plan", "facture"]

    data = parse_mission_md(mission_path)
    mission_id = data["meta"].get("id", mission_path.stem)
    output_dir = DOCS_DIR / mission_id
    output_dir.mkdir(parents=True, exist_ok=True)

    generators = {
        "devis": generate_devis,
        "plan": generate_plan_projet,
        "facture": generate_facture,
    }

    results = []
    for dtype in doc_types:
        if dtype not in generators:
            continue
        html = generators[dtype](data)
        filename = f"{dtype}-{mission_id}.html"
        path = output_dir / filename
        path.write_text(html, encoding="utf-8")
        results.append({
            "type": dtype,
            "mission_id": mission_id,
            "title": data["meta"].get("title", ""),
            "platform": data["meta"].get("platform", ""),
            "file": f"documents/{mission_id}/{filename}",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

    return results


def update_index(entries: list[dict]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = []
    for entry in entries:
        existing = [i for i, e in enumerate(index) if e.get("file") == entry["file"]]
        for i in reversed(existing):
            index.pop(i)
        index.insert(0, entry)
    index = index[:500]
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere des documents pro depuis une mission.")
    parser.add_argument("--mission", required=True, help="Chemin vers le fichier mission .md")
    parser.add_argument(
        "--type",
        default="all",
        choices=["devis", "plan", "facture", "all"],
        help="Type de document (default: all)",
    )
    args = parser.parse_args()

    mission_path = Path(args.mission)
    if not mission_path.exists():
        sys.stderr.write(f"ERREUR : fichier {mission_path} introuvable.\n")
        return 1

    types = ["devis", "plan", "facture"] if args.type == "all" else [args.type]
    results = generate_all(mission_path, types)
    update_index(results)

    for r in results:
        sys.stderr.write(f"[doc_gen] {r['type']} -> {r['file']}\n")
    sys.stdout.write(json.dumps(results, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
