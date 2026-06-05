# Commercial Agent - L-FDS

Agent commercial autonome pour la gestion CRM HubSpot, l'envoi d'emails et la strategie de prospection.

## Prerequisites

1. **Python 3.10+**
2. **Cle API Anthropic** : Creer un compte sur [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key
3. **Cle API HubSpot** : Settings → Integrations → Private Apps → Create private app
4. **Credentials Gmail API** : [Google Cloud Console](https://console.cloud.google.com) → APIs → Gmail API → Credentials

## Installation

```bash
cd commercial-agent
pip install -r requirements.txt
```

## Configuration

Copier le fichier `.env.example` en `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

## Lancement

```bash
python main.py
```

## Structure

```
commercial-agent/
├── main.py              # Point d'entree - boucle agent
├── config/
│   └── system_prompt.py # Prompt systeme de l'agent
├── tools/
│   ├── __init__.py
│   ├── hubspot.py       # Outils CRM HubSpot
│   ├── gmail.py         # Outils Gmail
│   ├── notion.py        # Outils Notion
│   ├── github_tools.py  # Outils GitHub
│   ├── livrables.py     # Generation de livrables
│   └── laposte.py       # Suivi d'envois La Poste (Colissimo/LRAR/Chronopost)
├── requirements.txt
└── .env.example
```

## Suivi La Poste

Le connecteur `tools/laposte.py` interroge l'API officielle "Suivi v2" de La Poste
(Colissimo, Lettre Recommandee / LRAR, Lettre Suivie, Chronopost).

1. Cle API gratuite : https://developer.laposte.fr → produit **Suivi v2**.
2. Renseigner `LAPOSTE_API_KEY` dans `.env` (en-tete `X-Okapi-Key`).
3. Usage ponctuel en CLI :

   ```bash
   python -m tools.laposte 07461145240
   ```

   Ou via l'agent : outil `laposte_track` (accepte une liste de numeros).
   La sortie est normalisee (statut, transporteur, dates, evenements) et prete
   a etre injectee dans un email Gmail, une note HubSpot ou une page Notion.
