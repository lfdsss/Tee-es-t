"""Update docs/status.json after a robot routine execution.

Called by GitHub Actions after each routine run.
Parses agent.log to extract metrics and updates the website status file.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime


logger = logging.getLogger("update_status")
logging.basicConfig(level=logging.INFO, format="%(levelname)s update_status: %(message)s")


STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "status.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "agent.log")
LIVRABLES_DIR = os.path.join(os.path.dirname(__file__), "livrables")


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
            "active_contacts": 0,
            "routines_this_week": 0,
            "activity": [],
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

        # Count tool calls
        tool_calls = re.findall(r"Tool: (\w+)", content)
        metrics["tools_called"] = tool_calls

        # Count email-related actions
        metrics["emails"] = len([t for t in tool_calls if "gmail" in t.lower()])
        metrics["drafts"] = len([t for t in tool_calls if "draft" in t.lower()])

        # Count CRM actions
        metrics["contacts"] = len([t for t in tool_calls if "hubspot" in t.lower()])

        # Check for errors
        metrics["errors"] = content.lower().count("[error]")

        # Check completion
        metrics["completed"] = "completed" in content.lower()

    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("Failed to parse %s: %s", LOG_FILE, exc)

    return metrics


def update_status(routine_name: str):
    """Update status.json with results from the latest routine."""
    status = load_status()
    metrics = parse_log()
    now = datetime.now().isoformat()

    # Update main fields
    status["last_run"] = now
    status["status"] = "Actif" if metrics["errors"] == 0 else "Erreur"
    status["emails_processed"] = status.get("emails_processed", 0) + metrics["emails"]
    status["routines_this_week"] = status.get("routines_this_week", 0) + 1

    if metrics["contacts"] > 0:
        status["active_contacts"] = metrics["contacts"]

    # Add activity entry
    time_str = datetime.now().strftime("%H:%M")
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

    # Keep last 20 activity entries
    activities = status.get("activity", [])
    activities.insert(0, activity_entry)
    status["activity"] = activities[:20]

    # Scan livrables directory for generated documents
    livrables_data = {"devis_count": 0, "propositions_count": 0, "total_montant": 0, "recent": []}
    if os.path.exists(LIVRABLES_DIR):
        for fname in sorted(os.listdir(LIVRABLES_DIR), reverse=True):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(LIVRABLES_DIR, fname), "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("type") == "devis":
                    livrables_data["devis_count"] += 1
                    livrables_data["total_montant"] += meta.get("total_ht", 0)
                elif meta.get("type") == "proposition":
                    livrables_data["propositions_count"] += 1
                    livrables_data["total_montant"] += meta.get("total_ht", 0)
                # Keep last 10 for display
                if len(livrables_data["recent"]) < 10:
                    livrables_data["recent"].append({
                        "type": meta.get("type", ""),
                        "date": meta.get("date", ""),
                        "client": meta.get("client", ""),
                        "objet": meta.get("objet", meta.get("titre", "")),
                        "montant": f"{meta.get('total_ht', 0):,.0f} EUR" if meta.get("total_ht") else None,
                    })
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping malformed livrable %s: %s", fname, exc)
                continue
    status["livrables"] = livrables_data

    # Reset weekly counter on Monday morning
    if datetime.now().weekday() == 0 and routine_name == "morning":
        status["routines_this_week"] = 1

    # Write updated status
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    print(f"Status updated: {routine_name} — {len(metrics['tools_called'])} tools called")


if __name__ == "__main__":
    routine = sys.argv[1] if len(sys.argv) > 1 else "morning"
    update_status(routine)
