# StudentFlow — CLAUDE.md

Plateforme de matching temps-réel entre jobs étudiants et profils étudiants.
Pensé comme "Uber pour jobs étudiants" : une offre arrive → scoring → notif
instantanée au meilleur candidat → accept en 1 clic.

## Architecture

```
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │  Scrapers    │───▶│  Matching    │───▶│  Notifier    │
 │  (agents)    │    │  Engine      │    │  (agents)    │
 └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
 ┌────────────────────────────────────────────────────┐
 │                   Supabase (Postgres)              │
 │   offers · students · matches · notifications      │
 └────────────────────────────────────────────────────┘
                          ▲
                          │
                 ┌────────┴────────┐
                 │  FastAPI HTTP   │
                 │  (students CRUD)│
                 └─────────────────┘
```

**3 agents** tournent en boucle indépendamment (voir `src/studentflow/agents.py`) :

1. **ScraperAgent** — appelle chaque source (`src/studentflow/scrapers/`) en
   parallèle avec isolation des erreurs, upsert dans `offers`. Intervalle
   par défaut : 15 min.
2. **MatcherAgent** — pour chaque nouvelle offre, calcule un score contre tous
   les étudiants actifs, écrit les matches > seuil dans `matches`. Intervalle :
   1 min.
3. **NotifierAgent** — prend les matches non-notifiés, envoie la notif (stub
   webhook pour l'instant), marque `notified_at`. Intervalle : 30 s.

## Modules

| Fichier                           | Rôle                                                |
| --------------------------------- | --------------------------------------------------- |
| `src/studentflow/config.py`       | Settings via `pydantic-settings` (env vars)         |
| `src/studentflow/models.py`       | Modèles Pydantic (Offer, Student, Match…)           |
| `src/studentflow/db.py`           | Client Supabase / repository pattern                |
| `src/studentflow/matching.py`     | Moteur de scoring pur (sans I/O)                    |
| `src/studentflow/scrapers/base.py`| Classe abstraite `BaseScraper`                      |
| `src/studentflow/scrapers/france_travail.py` | Scraper officiel via API publique        |
| `src/studentflow/scrapers/indeed.py` / `hellowork.py` / `studentjob.py` / `jobteaser.py` | Stubs propres à implémenter |
| `src/studentflow/agents.py`       | Boucles agent (scraper/matcher/notifier)            |
| `src/studentflow/api.py`          | FastAPI app + routes                                |
| `src/studentflow/cli.py`          | Entry points CLI (`studentflow run-api`, `run-agents`) |
| `schema.sql`                      | Schéma Postgres (Supabase)                          |

## Principes

- **Moteur de matching pur** : `matching.score(offer, student)` ne fait AUCUN
  I/O, est testé unitairement, et retourne un score ∈ [0, 1] + la liste des
  raisons. Ne jamais y mettre d'appel DB.
- **Scrapers isolés** : chaque scraper hérite de `BaseScraper` et implémente
  `async def fetch() -> list[Offer]`. Une exception dans un scraper ne doit
  jamais faire tomber les autres (cf. `ScraperAgent._run_one`).
- **DB = vérité** : les agents sont sans état. On peut les tuer/relancer
  n'importe quand, ils reprennent le travail via la DB.
- **Pas de LLM dans le hot path** : le matching est déterministe pour rester
  rapide (<10 ms par paire offre/étudiant en mémoire). Les LLMs peuvent
  enrichir les offres en batch, hors du chemin critique.

## Ajouter une source de scraping

1. Créer `src/studentflow/scrapers/<source>.py` qui hérite de `BaseScraper`.
2. Implémenter `async def fetch() -> list[Offer]`.
3. L'enregistrer dans `SCRAPERS` (liste dans `src/studentflow/scrapers/__init__.py`).
4. Ajouter un test dans `tests/test_scrapers.py` (avec `responses` ou
   `httpx_mock` pour stubber l'HTTP).

## Ajouter un critère de matching

1. Ajouter le champ dans `models.Offer` et/ou `models.Student`.
2. Écrire une fonction `_score_<critère>()` dans `matching.py`.
3. L'ajouter à `score()` avec un poids.
4. Ajouter des tests dans `tests/test_matching.py` couvrant match parfait,
   match partiel, no-match.

## Tests

`pytest` avec des fixtures claires (`tests/fixtures.py`). Le matching engine
est la partie la plus critique — vise >90% de couverture sur `matching.py`.

```bash
cd studentflow
make test              # run
make test-cov          # avec coverage
```
