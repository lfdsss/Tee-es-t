# commercial-agent — configurations de déploiement backup

## Runtime actif (production)

**`.github/workflows/robot.yml`** déclenche l'agent toutes les 10 minutes sur
GitHub Actions et commit `docs/status.json` dans le repo. C'est le seul
runtime exécuté en production.

## Configurations de fallback (non actives)

Les deux fichiers ci-dessous sont **conservés intentionnellement** mais ne
sont déclenchés par aucun pipeline. Ils servent de plan de migration prêt à
l'emploi si on quitte GitHub Actions un jour.

### `railway.json`

Définit un cron Railway unique (`40 6 * * 1-5`) qui exécute
`python autonomous.py morning`. Format JSON pur (pas de commentaires
possibles), donc le marquage backup vit ici, pas dans le fichier.

Pour l'activer :
1. Créer un service Railway pointant sur `commercial-agent/`.
2. Définir les secrets : `ANTHROPIC_API_KEY`, `HUBSPOT_API_KEY`,
   `GMAIL_CREDENTIALS_JSON`, `NOTION_API_KEY`, `GITHUB_TOKEN`,
   `AGENT_OWNER_*`, `HUBSPOT_OWNER_ID`.
3. Désactiver le cron `robot.yml` côté GitHub Actions pour éviter le double
   run.

Limite : un seul cron par fichier `railway.json`. Pour les routines
`followup` et `weekly_audit`, il faut créer des services Railway
additionnels avec un `startCommand` distinct.

### `render.yaml`

Définit **trois** crons Render distincts (morning / followup / weekly_audit)
avec leurs propres horaires et la même liste de secrets. Plus complet que
`railway.json`.

Pour l'activer :
1. Connecter le repo à Render et pointer Render vers ce fichier.
2. Renseigner les secrets marqués `sync: false` dans le dashboard Render.
3. Désactiver `robot.yml` côté GitHub Actions.

## Pourquoi on garde les deux

- **Pas de coût** : tant qu'aucun service Render/Railway n'est créé, ces
  fichiers ne facturent rien.
- **Plan B documenté** : si GitHub Actions devient un goulot (rate limits,
  pannes, coûts), la bascule prend ~30 min au lieu de tout reconstruire.
- **Référence des secrets** : `render.yaml` liste explicitement les variables
  d'environnement nécessaires à l'agent — utile comme documentation vivante.
