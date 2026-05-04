# StudentFlow Web

Tableau de bord React + TypeScript pour [StudentFlow](../studentflow).
Permet à un étudiant de s'inscrire et de consulter ses matches en temps réel
via l'API StudentFlow.

## Stack

- **Vite** + **React 18** + **TypeScript**
- **React Router v6** pour la navigation
- **Vitest** + **@testing-library/react** pour les tests
- Zéro framework UI — CSS vanilla, design sobre, dark mode par défaut
- Déploiement **Netlify** (ou n'importe quel hébergeur static)

## Développement local

```bash
cd studentflow-web
npm install
npm run dev              # http://localhost:5173
```

Le dev server proxyfie `/api/*` vers `http://localhost:8000` (API FastAPI).
Donc démarre en parallèle :

```bash
cd ../studentflow
make run-api
```

## Variables d'environnement

| Variable | Défaut | Usage |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | URL de base de l'API StudentFlow. En prod, pointer vers l'URL Railway du service `studentflow-api`, ex : `https://studentflow-api.up.railway.app` |

## Tests

```bash
npm run test           # vitest (components)
npm run typecheck      # tsc --noEmit
npm run lint           # eslint
```

## Build de production

```bash
npm run build          # génère dist/
npm run preview        # sert dist/ localement pour vérifier
```

## Déploiement Netlify

Le fichier `netlify.toml` à la racine de ce dossier contient toute la
configuration (base, build command, publish dir, redirections SPA). Sur
Netlify :

1. **Add new site** → **Import an existing project** → GitHub → `them311/Tee-es-t`
2. Base directory : `studentflow-web`
3. Build command : `npm run build`
4. Publish directory : `studentflow-web/dist`
5. Environment variables → ajouter `VITE_API_BASE_URL` pointant vers ton
   service Railway `studentflow-api`

Le déploiement se refait automatiquement à chaque push sur `main`.
