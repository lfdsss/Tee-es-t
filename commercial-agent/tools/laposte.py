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


# --- CLI : `python -m tools.laposte <numero> [<numero> ...]` ---

def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tools.laposte <numero_suivi> [<numero_suivi> ...]")
        raise SystemExit(2)
    try:
        for code in sys.argv[1:]:
            print(format_for_notification(track_shipment(code)))
    except AuthError as e:
        print(
            f"⚠️  {e}\n   Configure LAPOSTE_API_KEY (clé gratuite sur "
            "https://developer.laposte.fr — produit 'Suivi v2')."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
