"""La Poste tracking tools for the commercial agent.

Connecteur du suivi d'envois La Poste (Colissimo, Lettre Recommandée / LRAR,
Lettre Suivie, Chronopost) via l'API officielle "Suivi v2".

Architecture (cf. CLAUDE.md — scraping/data rules) :
  - `track_shipment()`      -> extraction brute (appel API authentifié)
  - `_normalize_shipment()` -> normalisation en JSON propre et réutilisable
  - `format_for_notification()` -> rendu humain (email / note CRM / Notion)

L'extraction et la normalisation sont volontairement séparées pour que la
sortie reste réutilisable par un webhook, un cron, ou l'orchestrateur d'agent.

Pré-requis : une clé API gratuite obtenue sur https://developer.laposte.fr
exposée via la variable d'environnement LAPOSTE_API_KEY (en-tête X-Okapi-Key).
"""

import json
import logging
import os

from .http_utils import AuthError, robust_request, validate_api_key

log = logging.getLogger("commercial-agent")

BASE_URL = "https://api.laposte.fr/suivi/v2"
WEB_TRACKING_URL = "https://www.laposte.fr/outils/suivre-vos-envois?code={code}"

# Codes "holder" -> transporteur, renvoyés par l'API La Poste.
_HOLDERS = {
    1: "La Poste",
    2: "Chronopost",
    3: "Colissimo",
    4: "La Poste (Courrier/Recommandé)",
    5: "DPD",
}


def _headers() -> dict:
    key = validate_api_key("LAPOSTE_API_KEY")
    return {
        "Accept": "application/json",
        "X-Okapi-Key": key,
    }


def _clean_code(code: str) -> str:
    """Normalise un numéro de suivi : retire espaces et met en majuscules.

    La Poste accepte 11 à 15 caractères (envois) ou 32 à 72 (avis de passage).
    """
    return (code or "").replace(" ", "").strip().upper()


def _normalize_shipment(payload: dict, code: str) -> dict:
    """Transforme la réponse brute de l'API en structure propre et stable.

    Tolérant aux champs manquants : l'API ne renvoie pas toujours toutes les
    clés (ex. un envoi pas encore pris en charge n'a ni `delivery` ni events).
    """
    shipment = payload.get("shipment", {}) or {}
    events = shipment.get("event", []) or []

    # Le dernier événement (le plus récent) porte le statut courant.
    last_event = events[0] if events else {}

    normalized_events = [
        {
            "date": ev.get("date"),
            "code": ev.get("code"),
            "label": ev.get("label"),
        }
        for ev in events
    ]

    holder = shipment.get("holder")
    return {
        "tracking_number": shipment.get("idShip") or code,
        "found": bool(shipment),
        "is_final": shipment.get("isFinal", False),
        "product": shipment.get("product"),
        "carrier": _HOLDERS.get(holder, "Inconnu") if holder is not None else None,
        "entry_date": shipment.get("entryDate"),
        "delivery_date": shipment.get("deliveryDate"),
        "current_status": last_event.get("label"),
        "current_status_date": last_event.get("date"),
        "events": normalized_events,
        "tracking_url": shipment.get("url")
        or WEB_TRACKING_URL.format(code=code),
    }


def track_shipment(code: str, lang: str = "fr_FR") -> dict:
    """Récupère et normalise le suivi d'un envoi La Poste.

    Returns un dict normalisé. En cas d'erreur "métier" (numéro inconnu, pas
    encore pris en charge), renvoie un dict avec `found=False` et `error`
    plutôt que de lever — pour rester utilisable en batch sans interrompre.
    """
    code = _clean_code(code)
    if not (11 <= len(code) <= 15 or 32 <= len(code) <= 72):
        return {
            "tracking_number": code,
            "found": False,
            "error": (
                "Format invalide : un numéro de suivi fait 11 à 15 caractères "
                "(ou 32 à 72 pour un avis de passage)."
            ),
            "tracking_url": WEB_TRACKING_URL.format(code=code),
        }

    url = f"{BASE_URL}/idships/{code}"
    try:
        resp = robust_request(
            "GET", url, headers=_headers(), params={"lang": lang}
        )
        return _normalize_shipment(resp.json(), code)
    except AuthError:
        # Propagée : c'est un problème de configuration, pas de l'envoi.
        raise
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 404:
            msg = "Aucun suivi trouvé (numéro inconnu ou envoi pas encore confié à La Poste)."
        elif status == 400:
            msg = "Numéro de suivi mal formé (rejeté par l'API La Poste)."
        else:
            msg = f"Erreur lors de l'appel à l'API La Poste : {e}"
        log.warning(f"La Poste tracking failed for {code}: {msg}")
        return {
            "tracking_number": code,
            "found": False,
            "error": msg,
            "tracking_url": WEB_TRACKING_URL.format(code=code),
        }


def format_for_notification(data: dict) -> str:
    """Rend un suivi normalisé en texte lisible (email, note CRM, Notion).

    Base du point 3 (notifications) : sortie prête à être injectée dans un
    email Gmail, une note HubSpot ou une page Notion.
    """
    code = data.get("tracking_number", "?")
    if not data.get("found"):
        return f"📦 {code} — {data.get('error', 'introuvable')}\n   Suivi : {data.get('tracking_url')}"

    status = data.get("current_status") or "Statut indisponible"
    date = data.get("current_status_date") or "?"
    carrier = data.get("carrier") or "La Poste"
    state = "✅ Livré" if data.get("is_final") else "🚚 En cours"
    lines = [
        f"📦 {code} — {state} ({carrier})",
        f"   Dernier statut : {status} ({date})",
        f"   Suivi : {data.get('tracking_url')}",
    ]
    return "\n".join(lines)


# --- Point 3 : moteur de notification / automatisation -------------------
#
# Unité d'automatisation composable (cf. CLAUDE.md — automation rules) :
# détecte les changements de statut par rapport à un état persistant et
# n'émet que les nouveautés. Déclenchable par cron, webhook ou agent.
# Aucune dépendance externe : état stocké en JSON sur le système de fichiers.

def _default_state_path() -> str:
    return os.getenv(
        "LAPOSTE_STATE_PATH", os.path.expanduser("~/.laposte_tracking.json")
    )


def _load_state(path: str) -> dict:
    """Charge l'état persistant {code: dernier_statut}. Tolérant : {} si absent/corrompu."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_state(path: str, state: dict) -> None:
    """Écrit l'état (best-effort, atomique via fichier temporaire)."""
    try:
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError as e:
        log.warning(f"Impossible d'écrire l'état La Poste ({path}): {e}")


def track_and_notify(codes, state_path=None, sink=None, lang="fr_FR") -> dict:
    """Suit une liste d'envois et n'émet que les statuts qui ont changé.

    - `state_path` : fichier JSON d'état (défaut : env LAPOSTE_STATE_PATH ou
      ~/.laposte_tracking.json).
    - `sink` : callable(str) appelé pour chaque changement (email, note CRM,
      page Notion, log…). Si None, aucun effet de bord — la liste est renvoyée.

    Returns {"changes": [...], "results": [...], "changed_count": int}.
    """
    state_path = state_path or _default_state_path()
    previous = _load_state(state_path)
    results = [track_shipment(c, lang=lang) for c in codes]

    changes = []
    new_state = dict(previous)
    for r in results:
        code = r.get("tracking_number", "")
        # Clé de comparaison : statut courant, ou message d'erreur si introuvable.
        signature = r.get("current_status") or r.get("error") or ""
        if previous.get(code) != signature:
            changes.append(r)
            if sink is not None:
                sink(format_for_notification(r))
        new_state[code] = signature

    _save_state(state_path, new_state)
    return {
        "changes": changes,
        "results": results,
        "changed_count": len(changes),
    }


# --- Tool Definitions (sent to Claude) ---

LAPOSTE_TOOLS = [
    {
        "name": "laposte_track",
        "description": (
            "Suit un ou plusieurs envois La Poste (Colissimo, Lettre Recommandée/LRAR, "
            "Lettre Suivie, Chronopost) via l'API officielle de suivi. Retourne le statut "
            "courant, le transporteur, les dates et l'historique des événements. "
            "Utiliser pour vérifier où en est un colis ou un recommandé."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "codes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste de numéros de suivi (11 à 15 caractères chacun).",
                },
                "lang": {
                    "type": "string",
                    "description": "Langue des libellés (défaut: fr_FR).",
                },
            },
            "required": ["codes"],
        },
    },
]


def execute_laposte_tool(name: str, input_data: dict) -> str:
    """Execute a La Poste tool and return the result as a string."""
    try:
        if name == "laposte_track":
            codes = input_data.get("codes") or []
            if isinstance(codes, str):
                codes = [codes]
            if not codes:
                return "Error: 'codes' est requis (liste de numéros de suivi)."
            lang = input_data.get("lang", "fr_FR")
            results = [track_shipment(c, lang=lang) for c in codes]
            summary = "\n".join(format_for_notification(r) for r in results)
            return json.dumps(
                {"summary": summary, "results": results},
                ensure_ascii=False,
                indent=2,
            )
        return f"Error: Unknown La Poste tool '{name}'"
    except AuthError as e:
        return (
            f"Error: {e}. Configure LAPOSTE_API_KEY (clé gratuite sur "
            "https://developer.laposte.fr, produit 'Suivi v2')."
        )
    except Exception as e:
        log.exception("La Poste tool failed")
        return f"Error executing {name}: {e}"


# --- CLI ---------------------------------------------------------------
#   Suivi ponctuel :  python -m tools.laposte <numero> [<numero> ...]
#   Veille (cron)  :  python -m tools.laposte --watch <numero> [<numero> ...]
#                     → n'affiche que les statuts qui ont changé depuis le
#                       dernier passage (état persistant).

def main() -> None:
    import sys

    args = sys.argv[1:]
    watch = False
    if args and args[0] in ("--watch", "-w"):
        watch = True
        args = args[1:]

    if not args:
        print(
            "Usage: python -m tools.laposte [--watch] <numero_suivi> [<numero_suivi> ...]"
        )
        raise SystemExit(2)

    try:
        if watch:
            res = track_and_notify(args, sink=print)
            if res["changed_count"] == 0:
                print("Aucun changement depuis le dernier passage.")
        else:
            for code in args:
                print(format_for_notification(track_shipment(code)))
    except AuthError as e:
        print(
            f"⚠️  {e}\n   Configure LAPOSTE_API_KEY (clé gratuite sur "
            "https://developer.laposte.fr — produit 'Suivi v2')."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
