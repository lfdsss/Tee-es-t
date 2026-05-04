# INTEGRATION — flux entre projets du monorepo

Ce dépôt héberge plusieurs projets sœurs qui se couplent via des contrats
implicites. Ce document rend ces contrats explicites pour éviter toute dérive
silencieuse au prochain déploiement.

## Vue d'ensemble

```
┌────────────────────────┐         ┌──────────────────────────┐
│  commercial-agent/     │  écrit  │  docs/status.json        │
│  (Python, cron Actions)│ ──────▶ │  docs/missions/*.md      │
└────────────────────────┘         └──────────────────────────┘
                                              │
                                              │ commit + push (robot.yml)
                                              ▼
                                   ┌──────────────────────────┐
                                   │  Netlify SNB site         │
                                   │  (publish: docs/)         │
                                   │  lit status.json côté     │
                                   │  client (fetch)           │
                                   └──────────────────────────┘

┌────────────────────────┐         ┌──────────────────────────┐
│  studentflow/          │  HTTP   │  studentflow-web/         │
│  (FastAPI, Railway)    │ ◀─────▶ │  (Vite+TS, Netlify)       │
└────────────────────────┘         └──────────────────────────┘
```

---

## Contrat 1 — `docs/status.json`

**Producteur unique** : `commercial-agent/update_status.py`
**Consommateurs** : `docs/index.html`, `docs/livrables.html`, `docs/pipeline.html`
**Trigger d'écriture** : `.github/workflows/robot.yml` (cron `*/10 * * * *`)
**Trigger de publication** : commit sur `main` → `netlify-deploy.yml`

### Schéma effectif

Champs **écrits par `update_status.py`** :

| Champ | Type | Description |
|---|---|---|
| `status` | `"Actif"` \| `"Erreur"` | Statut global de la dernière routine |
| `last_run` | ISO 8601 datetime | Timestamp de la dernière exécution |
| `emails_processed` | int (cumulatif) | Compteur total d'emails traités |
| `active_contacts` | int | Nombre de contacts CRM touchés (dernière run) |
| `routines_this_week` | int | Compteur hebdo (reset lundi matin) |
| `activity[]` | array (max 20) | Journal des dernières activités |
| `livrables` | object | `{devis_count, propositions_count, total_montant, recent[]}` |

Champs **persistés mais plus écrits** (legacy, lus par les pages) :

| Champ | Lecteur | Action recommandée |
|---|---|---|
| `active_companies` | `docs/index.html` | Réintroduire un script de sync HubSpot ou retirer de l'UI |
| `pipeline_value` | `docs/index.html:869` | Idem (fallback déjà géré côté UI sur `livrables.total_montant`) |
| `deals_count` | `docs/index.html:870` | Idem (fallback sur `livrables.propositions_count`) |
| `deals_by_stage` | `docs/index.html:926-937` | Idem |

Ces champs survivent grâce au pattern **load → merge → save** dans
`update_status.py:19-32` : les clés inconnues sont préservées telles quelles.
Ils se figent donc à leur dernière valeur connue.

### Schéma `activity[].type`

Les pages stylent les entrées en fonction de `type` :
- `"crm"` — action CRM
- `"email"` — emails traités
- `"systeme"` — erreur ou maintenance

### Règles d'évolution

- **Ajouter un champ** : OK, l'UI l'ignore tant qu'elle ne le lit pas.
- **Renommer un champ lu par l'UI** : nécessite mise à jour conjointe de
  `update_status.py` + des fichiers HTML qui le lisent (cf. tableau ci-dessus).
- **Supprimer un champ** : vérifier d'abord aucun lecteur dans `docs/*.html` ;
  retirer aussi du `load_status()` defaults dans `update_status.py:25-32`.

---

## Contrat 2 — `docs/missions/*.md`

**Producteur** : `commercial-agent/mission_responder.py`
**Consommateur** : `docs/missions.html` (liste statique servie par Netlify)
**Trigger** : workflow `mission-response.yml` ou appel manuel.

Les fichiers `.md` sont commitées tels quels. Tout fichier ajouté est servi à
l'URL `/missions/<slug>.md` par Netlify.

---

## Contrat 3 — StudentFlow API ↔ Web

**Backend** : `studentflow/` (FastAPI), déployé sur Railway.
**Frontend** : `studentflow-web/` (Vite+TS), déployé sur Netlify.

### Wiring

- Endpoint base URL exposé par `VITE_API_BASE_URL` (build-time).
  - Défaut : `https://studentflow-api.up.railway.app` (cf. `deploy-web.yml:51`).
  - Dev local : `/api` proxifié vers `http://localhost:8000` par `vite.config.ts`.
- CORS backend : `allow_origins=["*"]` (`studentflow/src/studentflow/api.py:47-51`).
- Endpoints + types : alignés 1:1 entre `studentflow/src/studentflow/api.py` et
  `studentflow-web/src/api.ts` (audit du 2026-04-23).

### Règles d'évolution

- **Toute modification d'endpoint** doit être appliquée des deux côtés dans le
  **même commit** :
  - `studentflow/src/studentflow/{api.py, models.py, schema.sql}` (backend)
  - `studentflow-web/src/{api.ts, types.ts}` (frontend)
- Un smoke test contract vit dans `studentflow-web/src/api.contract.test.ts` :
  toute déserialisation d'une réponse fixture doit y rester valide.

---

## Contrat 4 — Variables d'environnement partagées

| Variable | Utilisateurs | Notes |
|---|---|---|
| `HUBSPOT_API_KEY` | `server/hubspot.js` (SNB), `commercial-agent/tools/hubspot.py` | Rotation = à propager des deux côtés |
| `NETLIFY_AUTH_TOKEN` | `netlify-deploy.yml`, `deploy-web.yml` | Un seul token, deux sites distincts |
| `NETLIFY_SITE_ID` | `netlify-deploy.yml` (secret) | Site SNB. studentflow-web a son propre ID hardcodé `75402425-…` |
| `RAILWAY_TOKEN` | `deploy-api.yml`, `configure-railway.yml` | Backend studentflow uniquement |
| `ANTHROPIC_API_KEY`, `GMAIL_*`, `NOTION_API_KEY`, `GITHUB_TOKEN` | `robot.yml` → commercial-agent | Cf. `commercial-agent/render.yaml` pour la liste exhaustive |

---

## Topologie de déploiement (résumé)

| Surface | Config active | CI | Configs backup (non actives) |
|---|---|---|---|
| SNB site (LFDS quiz + portfolio) | `netlify.toml` | `netlify-deploy.yml` | `fly.toml`, `Dockerfile`, `deploy-fly.sh` (manuel) |
| commercial-agent | `.github/workflows/robot.yml` | cron `*/10 * * * *` | `commercial-agent/railway.json`, `commercial-agent/render.yaml` |
| studentflow API | `studentflow/railway.toml` + `Procfile` | `deploy-api.yml` | — |
| studentflow web | `studentflow-web/netlify.toml` | `deploy-web.yml` | — |

Les configs marquées "backup" sont conservées intentionnellement comme
fallback en cas de migration depuis GitHub Actions ; elles ne sont pas
exécutées en production.

---

## Intégration LFDS Quiz → l-fds.com

Le quiz « Quel gourmet êtes-vous ? » est buildé par `netlify-deploy.yml` à
chaque push touchant `src/`, `index.html` ou `vite.config.js`, puis publié
dans `docs/quiz/` côté Netlify. Il est donc accessible publiquement à
**`https://<netlify-site>/quiz/`** où `<netlify-site>` est l'URL du site
Netlify SNB (l'ID est dans le secret `NETLIFY_SITE_ID`).

### Snippets prêts à coller dans l-fds.com

Cinq méthodes d'intégration sont documentées et prêtes à copier-coller dans
**`docs/lfds-quiz-embed.html`** (servi à `/lfds-quiz-embed`) :

1. **Bouton CTA** — coller dans header / hero / footer.
2. **Bandeau hero plein largeur** — section conversion-friendly.
3. **Iframe embed** — quiz inline dans une page existante.
4. **Tracking UTM** — les paramètres sont capturés par `/api/admin/submissions`.
5. **Sous-domaine personnalisé `quiz.l-fds.com`** — Netlify + CNAME DNS.

### Procédure de mise en prod (recommandée)

1. **Récupérer l'URL Netlify courante** du site SNB (Netlify dashboard →
   Sites → identifier le site dont l'ID matche `secrets.NETLIFY_SITE_ID`).
2. **Configurer le sous-domaine** `quiz.l-fds.com` côté DNS du registrar
   l-fds.com :
   ```
   Type: CNAME    Nom: quiz    Cible: <site>.netlify.app
   ```
   Puis dans Netlify : Site settings → Domain management → Add custom domain
   → `quiz.l-fds.com`. HTTPS auto via Let's Encrypt (≈ 1 min).
3. **Coller le snippet choisi** (idéalement #1 ou #2) dans le template du
   site l-fds.com en remplaçant `https://lfds-quiz.netlify.app/quiz/` par
   `https://quiz.l-fds.com/quiz/`.
4. **Vérifier** : le quiz s'ouvre, les soumissions remontent dans
   `/api/admin/submissions` du serveur Fly (`lfds-quiz` app).

### Backend du quiz (collecte des leads)

Le quiz POST ses soumissions vers `/api/quiz/submit` exposé par
`server/index.js` (Express, déployé sur **Fly.io**, app `lfds-quiz`, region
`cdg`, volume persistant `quiz_data` monté sur `/app/server/data`). Tant
que cette app Fly tourne, les leads sont stockés ; si on l'arrête, le
quiz côté front fonctionne mais les soumissions sont perdues.

Pour interroger les leads :
```
GET https://lfds-quiz.fly.dev/api/admin/submissions
Header: x-api-key: $LFDS_API_KEY
```
