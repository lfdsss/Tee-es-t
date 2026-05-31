# HANDOFF — Reprise de session SNB Consulting + LFDS

> **Comment utiliser ce fichier** : copie-colle tout son contenu au début
> d'une nouvelle conversation Claude Code (ou attache-le). Il contient tout
> le contexte nécessaire pour reprendre le travail sans rien réexpliquer.

---

## 1. Contexte projet

Monorepo **`them311/Tee-es-t`** (remote `origin`) regroupant 4 sous-projets,
2 marques distinctes :

- **SNB Consulting** (priorité) — agence IA/automatisation. Site vitrine +
  dashboard live alimenté par un agent commercial Python.
- **La Française des Sauces (LFDS)** — marque de sauces premium. Site
  vitrine/boutique + quiz + site de recettes.

**Branche de travail** : `claude/explore-project-structure-Z6s71`
**Remote à utiliser** : `origin` (`https://github.com/lfdsss/Tee-es-t` côté
CLAUDE.md ; le dépôt `bpthevenot-hub/teest` est à IGNORER).
**Email user** : bp.thevenot@gmail.com

---

## 2. Les 3 directives NON-NÉGOCIABLES

1. **SNB est le projet le plus puissant.** Il reflète toutes les
   améliorations, a des visuels parlants (même pour les briques non
   déployées), et le code le plus solide. Reste sur **Netlify** (pas WP) —
   ce qui le rend puissant c'est le `commercial-agent`, pas l'hébergeur.
2. **Ne JAMAIS mélanger SNB et LFDS.** 2 marques, infrastructures séparées,
   deploys séparés, zéro dépendance croisée.
3. **LFDS doit lier (a) le quiz existant et (b) le site de recettes.**

---

## 3. État du repo — ce qui est LIVRÉ et poussé

Tous ces commits sont sur `origin/claude/explore-project-structure-Z6s71` :

| Commit | Sprint | Contenu |
|--------|--------|---------|
| `84b105a` | 1 | SNB : hero live stats animées + panel "Preuves" + refresh portfolio |
| `97ad6ae` | 2 | SNB : `docs/devis-instant.html` + Netlify Functions `devis-generate.js` & `lead-capture.js` (HubSpot) |
| `172fe86` | 3 | LFDS recettes : bootstrap React/Vite + 12 recettes seed + filtres + modal |
| `2b6984c` | 5 | LFDS recettes : générateur IA Claude (`recipe-generate.js` + `RecipeGenerator.jsx` + onglet) |
| `32c1f5b` | 4 | LFDS : runbook `docs/LFDS_WP_MIGRATION.md` (migration WP+WooCommerce) |
| `df04fdd` | — | Refactor : centralisation des constantes profils dans `recettes/src/data/profiles.js` (build vite vérifié) |

> ⚠️ **Note environnement** : la copie locale peut avoir été réinitialisée
> sur un commit "Robot: mise a jour statut" (le cron `commercial-agent`
> commit `docs/status.json` toutes les 10 min). Pour récupérer le travail :
> `git fetch origin claude/explore-project-structure-Z6s71 && git checkout claude/explore-project-structure-Z6s71`

---

## 4. Architecture des sous-projets

```
Tee-es-t/
├── commercial-agent/      # Python + Claude SDK. Cron GitHub Actions */10.
│                          # Écrit docs/status.json, docs/documents/*, docs/missions/*
├── docs/                  # SNB Consulting — site statique Netlify
│                          #   → snbbm-consulting.com (snb-consulting-platform.netlify.app)
│                          #   index.html, portfolio.html, devis-instant.html, etc.
│                          #   LFDS_WP_MIGRATION.md (runbook ops)
├── netlify/functions/     # Functions SNB : devis-generate.js, lead-capture.js,
│                          #   quiz-submit.js, admin-*.js, health.js
├── src/ + server/         # Quiz LFDS (React/Vite front + backend Fly.io)
│                          #   → quiz.l-fds.com (Netlify) + app Fly "lfds-quiz"
│                          #   INTACT — ne pas toucher
└── recettes/              # LFDS Recettes — NOUVEAU sous-projet React/Vite
    │                      #   → destiné à recettes.l-fds.com (Netlify dédié)
    ├── netlify.toml       #   base=recettes/, publish=recettes/dist
    ├── netlify/functions/recipe-generate.js   # Claude API generator
    └── src/
        ├── data/
        │   ├── recipes.json    # 12 recettes éditoriales (4×épicurien/artisan/pragmatique)
        │   └── profiles.js     # SOURCE UNIQUE des constantes profils + occasions
        └── components/
            ├── RecipeApp.jsx       # tab switcher Bibliothèque ↔ Générateur
            ├── RecipeCard.jsx, RecipeDetail.jsx, RecipeFilter.jsx
            └── RecipeGenerator.jsx # formulaire IA
```

**3 sites Netlify distincts** (cloisonnement) : SNB (`docs/`), Quiz LFDS
(`src/`), Recettes LFDS (`recettes/`). + 1 backend Fly.io (quiz). + bientôt
1 WP O2switch (vitrine/boutique LFDS).

---

## 5. Contrats techniques clés

### `docs/status.json` (écrit par commercial-agent, lu par docs/*.html)
Champs : `status`, `last_run`, `emails_processed`, `active_contacts`,
`routines_this_week`, `activity[]`, `livrables{}`, `pipeline_value`,
`deals_count`, `deals_by_stage`. Le hero SNB l'anime via `fetch()`.

### `recettes/src/data/recipes.json` (schema par recette)
```json
{ "id", "title", "description",
  "profile": "epicurien|artisan|pragmatique",
  "sauce_name", "sauce_url": "https://l-fds.com/<profile>",
  "emoji", "occasion": "quotidien|weekend|reception|express",
  "difficulty": 1|2|3, "time_min", "servings",
  "ingredients": [], "steps": [], "tip"?, "tags": [] }
```

### Endpoints Netlify Functions
- `POST /api/devis-generate` (SNB) — génère HTML devis. Valide days[0.5-60],
  tjm[200-2500], mission_type whitelist.
- `POST /api/lead-capture` (SNB) — upsert HubSpot (POST→409 PATCH) + GitHub
  `repository_dispatch` event `lead_captured`.
- `POST /api/recipe-generate` (Recettes) — Claude `claude-sonnet-4-6`.
  Valide profile whitelist, ingredients[1-12], servings[1-8], occasion.

### Variables d'environnement à configurer (côté dashboards)
| Var | Site | Requis |
|-----|------|--------|
| `HUBSPOT_API_KEY` | Netlify SNB | oui (lead-capture/devis) |
| `GITHUB_DISPATCH_TOKEN` + `GITHUB_REPO=them311/Tee-es-t` | Netlify SNB | optionnel (trigger agent) |
| `ANTHROPIC_API_KEY` | Netlify Recettes | oui (générateur IA) |

---

## 6. CE QUI RESTE À FAIRE

### Actions plateforme (manuelles, hors code)
1. **Déconnecter Vercel** : `https://vercel.com/snb1/tee-es-t` → Settings →
   Git → Disconnect. (Vercel auto-détecte mal le monorepo → status rouge sur
   les PR. Le vrai deploy est Netlify. Aucune modif repo nécessaire.)
2. **Créer le site Netlify Recettes** : base `recettes/`, var `ANTHROPIC_API_KEY`.
3. **Vars Netlify SNB** : `HUBSPOT_API_KEY`, et si souhaité
   `GITHUB_DISPATCH_TOKEN` + `GITHUB_REPO`.

### Sprint 4 — Migration WP LFDS (ops, suivre le runbook)
`docs/LFDS_WP_MIGRATION.md` détaille les 7 étapes : O2switch (~84€/an) →
WP+Kadence+WooCommerce → pages critiques (`/epicurien`, `/artisan`,
`/pragmatique` = slugs des redirections quiz, NON-NÉGOCIABLES) → embed quiz
+ recettes en iframe → bascule DNS → tests E2E → rollback.
**Coût total cible LFDS : ~150-200€/an. SNB : ~0€.**

### Améliorations identifiées (review "simplify", non bloquantes)
- **Rate limiting `recipe-generate.js`** : actuellement aucun → risque de
  spam coûteux en tokens. À ajouter via Netlify Edge Rate Limit ou
  Cloudflare AVANT trafic significatif.
- Helpers de réponse JSON partagés entre Netlify Functions : volontairement
  PAS factorisés (créerait un import cross-projet cassant le cloisonnement).

---

## 7. Règles de contribution (CLAUDE.md)

- **Jamais de push direct sur `main`** — toujours branche + PR.
- **Pas de PR sans demande explicite** du user.
- **Pas de suppression/déplacement de fichier sans validation humaine.**
- Lire avant de modifier : `README.md`, `package.json`,
  `studentflow/pyproject.toml`, les `requirements.txt`, `.github/workflows/*`.
- Mode `/auto` actif : opérateur autonome, propose la prochaine action à
  fort impact, ne demande confirmation que pour actions destructives/ambiguës.

---

## 8. Prompt de reprise suggéré

> « Reprends le travail sur la branche `claude/explore-project-structure-Z6s71`
> du repo `them311/Tee-es-t`. Les sprints 1-5 (SNB visuel + devis-instant,
> recettes LFDS bibliothèque + générateur IA, runbook WP) sont livrés et
> poussés. Fais d'abord `git fetch origin claude/explore-project-structure-Z6s71
> && git checkout` puis `git merge` ou rebase si besoin. Prochaine priorité :
> [au choix] (a) ajouter le rate limiting sur recipe-generate.js, (b) dérouler
> le Sprint 4 migration WP, ou (c) ce que je te dirai. Respecte les 3
> directives : SNB le plus puissant, ne pas mélanger SNB/LFDS, lier quiz +
> recettes à LFDS. »
