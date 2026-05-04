# StudentFlow

Matching temps-réel entre offres d'emploi étudiantes et profils étudiants.
Trois agents Python autonomes scrappent les sources, scorent les offres contre
les profils, et notifient instantanément le meilleur candidat.

> **État** : MVP opérationnel. Moteur de matching testé. Scraper France Travail
> fonctionnel, autres sources en stubs propres à étendre.

## Quickstart

```bash
cd studentflow
make install
cp .env.example .env      # puis éditer
make test                 # vérifier l'installation
make run-api              # démarre l'API FastAPI sur :8000
make run-agents           # démarre les 3 agents en boucle
```

## Architecture

```
Scrapers  ──▶  Matching engine  ──▶  Notifier
   │                │                   │
   ▼                ▼                   ▼
         Supabase (Postgres)
                ▲
          FastAPI HTTP
```

Trois agents tournent en boucle indépendamment :

| Agent          | Intervalle | Rôle                                               |
| -------------- | ---------- | -------------------------------------------------- |
| ScraperAgent   | 15 min     | Appelle chaque source en parallèle, upsert offers  |
| MatcherAgent   | 1 min      | Score les nouvelles offres contre les étudiants    |
| NotifierAgent  | 30 s       | Envoie les notifs des matches non-notifiés         |

Voir [`CLAUDE.md`](./CLAUDE.md) pour l'architecture détaillée et les conventions.

## Modèle de données

Quatre tables principales :

- `offers` — offres scrappées (source, titre, description, localisation, contrat, skills, remote…)
- `students` — profils étudiants (skills, ville, remote_ok, disponibilités, contrats souhaités…)
- `matches` — score + raisons, fait le lien offer ↔ student
- `notifications` — log des notifs envoyées (idempotence)

Schéma complet dans [`schema.sql`](./schema.sql).

## Moteur de matching

Fonction pure sans I/O : `studentflow.matching.score(offer, student) -> MatchResult`.
Le score est une pondération déterministe de plusieurs critères :

| Critère       | Poids | Logique                                             |
| ------------- | ----- | --------------------------------------------------- |
| Skills        | 0.40  | Overlap Jaccard entre skills offer et student       |
| Localisation  | 0.25  | Ville identique OU remote compatible                |
| Contrat       | 0.15  | Type (stage/alternance/cdd/part-time) compatible    |
| Heures/sem    | 0.10  | Dans la fenêtre max_hours_per_week étudiant         |
| Disponibilité | 0.10  | Overlap entre available_from/until et offer dates   |

Chaque composant est testable indépendamment. Ajouter un critère : voir
`CLAUDE.md` section "Ajouter un critère de matching".

## Déploiement

- **Supabase** : créer un projet, exécuter `schema.sql` dans le SQL editor,
  récupérer `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`.
- **Railway** : fichier `railway.toml` fourni. Les deux process (API + agents)
  sont définis dans `Procfile`. Configurer les env vars depuis `.env.example`.
- **France Travail API** : créer une app sur
  [francetravail.io](https://francetravail.io/inscription) et récupérer
  `CLIENT_ID` / `CLIENT_SECRET`.

## Licence

Apache-2.0 — voir [`../LICENSE`](../LICENSE).
