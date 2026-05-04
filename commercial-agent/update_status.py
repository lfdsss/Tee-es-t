"""Update docs/status.json after a robot routine execution.

Called by GitHub Actions after each routine run.
Parses agent.log to extract metrics, fetches live CRM data,
and updates the website status file with all dashboard sections.
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "status.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "agent.log")
LIVRABLES_DIR = os.path.join(os.path.dirname(__file__), "livrables")
HUBSPOT_BASE = "https://api.hubapi.com"


def _hs_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.getenv('HUBSPOT_API_KEY', '')}",
        "Content-Type": "application/json",
    }


def load_status() -> dict:
    """Load existing status or return defaults."""
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "status": "Actif",
            "last_run": None,
            "emails_processed": 0,
            "emails_processed_date": None,
            "active_contacts": 0,
            "routines_this_week": 0,
            "activity": [],
            "livrables": {"devis_count": 0, "propositions_count": 0, "total_montant": 0, "recent": []},
            "contacts": [],
            "deals": [],
            "missions": [],
            "budget": {
                "ca_total": 0, "pipeline_value": 0, "expenses": 0,
                "margin_percent": 0, "acceptance_rate": 0,
                "ca_mensuel": [], "transactions": [],
            },
        }


def parse_log() -> dict:
    """Parse agent.log to extract useful metrics."""
    metrics = {
        "emails": 0,
        "drafts": 0,
        "contacts": 0,
        "tools_called": [],
        "errors": 0,
        "completed": False,
    }

    if not os.path.exists(LOG_FILE):
        return metrics

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        tool_calls = re.findall(r"Tool: (\w+)", content)
        metrics["tools_called"] = tool_calls
        metrics["emails"] = len([t for t in tool_calls if "gmail" in t.lower()])
        metrics["drafts"] = len([t for t in tool_calls if "draft" in t.lower()])
        metrics["contacts"] = len([t for t in tool_calls if "hubspot" in t.lower()])
        metrics["errors"] = content.lower().count("[error]")
        metrics["completed"] = "completed" in content.lower()
    except Exception:
        pass

    return metrics


def fetch_hubspot_contacts() -> list:
    """Fetch active contacts from HubSpot CRM."""
    if not requests or not os.getenv("HUBSPOT_API_KEY"):
        return []

    resp = requests.post(
        f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
        headers=_hs_headers(),
        json={
            "limit": 50,
            "properties": [
                "firstname", "lastname", "email", "phone", "company",
                "lifecyclestage", "hs_lead_status", "createdate", "lastmodifieddate",
            ],
        },
        timeout=15,
    )
    resp.raise_for_status()

    contacts = []
    for c in resp.json().get("results", []):
        p = c.get("properties", {})
        contacts.append({
            "id": f"hs_{c['id']}",
            "firstname": p.get("firstname", ""),
            "lastname": p.get("lastname", ""),
            "email": p.get("email", ""),
            "phone": p.get("phone", ""),
            "company": p.get("company", ""),
            "lifecyclestage": p.get("lifecyclestage", "lead"),
            "hs_lead_status": p.get("hs_lead_status", "NEW"),
            "last_activity": p.get("lastmodifieddate", ""),
            "created_at": p.get("createdate", ""),
        })
    return contacts


def fetch_hubspot_deals() -> list:
    """Fetch deals from HubSpot pipeline."""
    if not requests or not os.getenv("HUBSPOT_API_KEY"):
        return []

    resp = requests.post(
        f"{HUBSPOT_BASE}/crm/v3/objects/deals/search",
        headers=_hs_headers(),
        json={
            "limit": 50,
            "properties": ["dealname", "amount", "dealstage", "closedate"],
        },
        timeout=15,
    )
    resp.raise_for_status()

    deals = []
    for d in resp.json().get("results", []):
        p = d.get("properties", {})
        deals.append({
            "id": f"deal_{d['id']}",
            "dealname": p.get("dealname", ""),
            "amount": float(p.get("amount", 0) or 0),
            "dealstage": p.get("dealstage", ""),
            "closedate": (p.get("closedate") or "")[:10],
        })
    return deals


DEAL_STAGE_PROGRESS = {
    "appointmentscheduled": 10,
    "qualifiedtobuy": 30,
    "presentationscheduled": 50,
    "decisionmakerboughtin": 70,
    "contractsent": 90,
    "closedwon": 100,
    "closedlost": 0,
}


def build_missions(deals: list, livrables: dict) -> list:
    """Derive missions from active deals."""
    today = datetime.now().strftime("%Y-%m-%d")
    missions = []
    for d in deals:
        stage = d.get("dealstage", "")
        if stage in ("closedlost",):
            continue
        progress = DEAL_STAGE_PROGRESS.get(stage, 20)
        status = "termine" if stage == "closedwon" else "en_cours"
        if status != "termine" and d.get("closedate") and d["closedate"] < today:
            status = "en_retard"
        if progress <= 10:
            status = "planifie"

        missions.append({
            "id": f"mission_{d['id']}",
            "name": d.get("dealname", "Mission"),
            "client": "",
            "status": status,
            "progress": progress,
            "start_date": "",
            "end_date": d.get("closedate", ""),
            "deliverables": [],
            "deal_id": d["id"],
        })
    return missions


def build_budget(deals: list, livrables: dict) -> dict:
    """Build budget data from deals and livrables."""
    won = [d for d in deals if d.get("dealstage") == "closedwon"]
    lost = [d for d in deals if d.get("dealstage") == "closedlost"]
    pipeline = [d for d in deals if d.get("dealstage") not in ("closedwon", "closedlost")]

    ca_total = sum(d.get("amount", 0) for d in won)
    pipeline_value = sum(d.get("amount", 0) for d in pipeline)
    ca_total += livrables.get("total_montant", 0) if not won else 0

    expenses_file = os.path.join(os.path.dirname(__file__), "config", "expenses.json")
    expenses = 0
    if os.path.exists(expenses_file):
        try:
            with open(expenses_file, "r", encoding="utf-8") as f:
                expenses = json.load(f).get("total", 0)
        except (json.JSONDecodeError, IOError):
            pass

    margin = round((ca_total - expenses) / ca_total * 100) if ca_total > 0 else 0
    total_decided = len(won) + len(lost)
    acceptance_rate = round(len(won) / total_decided * 100) if total_decided > 0 else 0

    monthly = defaultdict(float)
    month_names = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Avr", 5: "Mai",
                   6: "Jun", 7: "Jul", 8: "Aou", 9: "Sep", 10: "Oct",
                   11: "Nov", 12: "Dec"}
    for d in won:
        cd = d.get("closedate", "")
        if cd and len(cd) >= 7:
            try:
                m = int(cd[5:7])
                monthly[m] += d.get("amount", 0)
            except ValueError:
                pass

    ca_mensuel = [{"mois": month_names.get(m, str(m)), "montant": int(v)}
                  for m, v in sorted(monthly.items())]

    transactions = []
    for d in sorted(won + lost, key=lambda x: x.get("closedate", ""), reverse=True)[:10]:
        if d.get("dealstage") == "closedwon":
            transactions.append({
                "date": d.get("closedate", ""),
                "type": "revenu",
                "description": d.get("dealname", ""),
                "montant": d.get("amount", 0),
            })

    return {
        "ca_total": int(ca_total),
        "pipeline_value": int(pipeline_value),
        "expenses": int(expenses),
        "margin_percent": margin,
        "acceptance_rate": acceptance_rate,
        "ca_mensuel": ca_mensuel,
        "transactions": transactions,
    }


def scan_livrables() -> dict:
    """Scan livrables directory for generated documents."""
    data = {"devis_count": 0, "propositions_count": 0, "total_montant": 0, "recent": []}
    if not os.path.exists(LIVRABLES_DIR):
        return data

    for fname in sorted(os.listdir(LIVRABLES_DIR), reverse=True):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(LIVRABLES_DIR, fname), "r", encoding="utf-8") as f:
                meta = json.load(f)
            doc_type = meta.get("type", "")
            if doc_type == "devis":
                data["devis_count"] += 1
                data["total_montant"] += meta.get("total_ht", 0)
            elif doc_type == "proposition":
                data["propositions_count"] += 1
                data["total_montant"] += meta.get("total_ht", 0)

            if len(data["recent"]) < 10:
                data["recent"].append({
                    "id": meta.get("numero", meta.get("reference", fname)),
                    "type": doc_type,
                    "date": meta.get("date", ""),
                    "client": meta.get("client", ""),
                    "objet": meta.get("objet", meta.get("titre", "")),
                    "montant": f"{meta.get('total_ht', 0):,.0f} EUR" if meta.get("total_ht") else None,
                    "status": "envoye",
                    "total_ht": meta.get("total_ht", 0),
                    "total_ttc": meta.get("total_ttc", 0),
                })
        except (json.JSONDecodeError, IOError):
            continue
    return data


def update_status(routine_name: str):
    """Update status.json with results from the latest routine."""
    status = load_status()
    metrics = parse_log()
    now = datetime.now()

    # Core fields
    status["last_run"] = now.isoformat()
    status["status"] = "Actif" if metrics["errors"] == 0 else "Erreur"
    status["routines_this_week"] = status.get("routines_this_week", 0) + 1

    # Email metric with daily reset
    today_str = now.strftime("%Y-%m-%d")
    if status.get("emails_processed_date") != today_str and routine_name == "morning":
        status["emails_processed"] = 0
    status["emails_processed_date"] = today_str
    status["emails_processed"] = status.get("emails_processed", 0) + metrics["emails"]

    # Activity entry
    time_str = now.strftime("%H:%M")
    routine_labels = {
        "morning": "Routine du matin",
        "followup": "Relances prospects",
        "weekly_audit": "Audit hebdomadaire",
    }
    label = routine_labels.get(routine_name, routine_name)

    activity_entry = {
        "time": time_str,
        "type": "crm",
        "message": f"{label} terminee - {len(metrics['tools_called'])} actions executees",
    }
    if metrics["emails"] > 0:
        activity_entry["type"] = "email"
        activity_entry["message"] += f", {metrics['emails']} emails traites"
    if metrics["errors"] > 0:
        activity_entry["type"] = "systeme"
        activity_entry["message"] = f"{label} terminee avec {metrics['errors']} erreur(s)"

    activities = status.get("activity", [])
    activities.insert(0, activity_entry)
    status["activity"] = activities[:20]

    # Livrables
    livrables_data = scan_livrables()
    status["livrables"] = livrables_data

    # HubSpot contacts
    try:
        contacts = fetch_hubspot_contacts()
        status["contacts"] = contacts
        status["active_contacts"] = len(contacts)
    except Exception:
        status.setdefault("contacts", [])
        if metrics["contacts"] > 0:
            status["active_contacts"] = metrics["contacts"]

    # HubSpot deals
    deals = []
    try:
        deals = fetch_hubspot_deals()
        status["deals"] = deals
    except Exception:
        deals = status.get("deals", [])
        status.setdefault("deals", [])

    # Missions
    status["missions"] = build_missions(deals, livrables_data)

    # Budget
    status["budget"] = build_budget(deals, livrables_data)

    # Weekly counter reset on Monday morning
    if now.weekday() == 0 and routine_name == "morning":
        status["routines_this_week"] = 1

    # Write
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Status updated: {routine_name} — {len(metrics['tools_called'])} tools called")


if __name__ == "__main__":
    routine = sys.argv[1] if len(sys.argv) > 1 else "morning"
    update_status(routine)
