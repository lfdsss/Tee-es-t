# StudentFlow — déploiement

Guide pratique pour passer le MVP StudentFlow en production. Temps réel
estimé si tu crées les comptes depuis zéro : **~30 minutes**. Si les comptes
existent déjà : **~10 minutes**.

La stack recommandée est **Supabase (DB) + Railway (API + worker)** parce
qu'elle demande zéro DevOps, facture au seul usage, et déploie par `git push`.
Tout le code fonctionne aussi en local sans aucun compte grâce au fallback
`InMemoryRepository`.

---

## 1. Pré-requis (5 min)

Crée ces 4 comptes dans l'ordre et garde les clés à portée de main :

| Service | Lien | Ce que tu récupères | Coût |
|---|---|---|---|
| Supabase | https://supabase.com | `SUPABASE_URL` + `service_role` key | Gratuit |
| France Travail | https://francetravail.io | `CLIENT_ID` + `CLIENT_SECRET` | Gratuit |
| Adzuna | https://developer.adzuna.com | `APP_ID` + `APP_KEY` | Gratuit (1k/mois) |
| Railway | https://railway.app | Compte GitHub | ~5 €/mois |

**Important Supabase** : prends la clé **`service_role`** (jamais la `anon`).
StudentFlow tourne côté serveur et contourne RLS pour écrire en DB.

**Important France Travail** : une fois ton compte créé, il faut
explicitement s'abonner à l'API *"Offres d'emploi v2"* depuis le dashboard.
Sinon le token OAuth sera valide mais les appels renverront 403.

---

## 2. Création du schéma Supabase (2 min)

1. Ouvre ton projet Supabase → **SQL Editor** → **New query**.
2. Copie-colle le contenu intégral de [`schema.sql`](./schema.sql).
3. Run. Tu dois voir 4 tables créées : `offers`, `students`, `matches`, `notifications`.
4. Vérifie dans **Table Editor** que les index et RLS sont bien là.

Le script est **idempotent** — tu peux le relancer autant de fois que tu
veux, il ne cassera rien.

---

## 3. Test en local (3 min)

Avant de déployer, valide que ta machine voit tout correctement :

```bash
cd studentflow
cp .env.example .env
# → édite .env avec les vraies clés des 3 services

make install        # pip install -e .[dev]
make test           # 36 tests doivent passer
```

Puis smoke test de bout en bout **sans attendre les loops** :

```bash
# Insère 2 étudiants de démo (Lucas / Sarah)
python -m studentflow.cli seed-demo

# Lance UN tour de chaque agent (scrape → match → notify) et sors
python -m studentflow.cli tick
```

Tu dois voir dans les logs quelque chose comme :
```
Scraper tick: 47 offers upserted
Matcher tick: 3 matches created
Notifier tick: 3 notifications processed
```

Si le scraper retourne 0, vérifie que tes clés Adzuna/France Travail sont
correctes — les scrapers loggent `not configured; skipping` quand elles
manquent, ce qui est un bon signe côté code mais pas côté prod.

---

## 4. Déploiement Railway (10 min)

Railway peut builder soit directement depuis `pyproject.toml` via Nixpacks
(ce qui est déjà configuré dans `railway.toml`), soit depuis le `Dockerfile`
si tu veux plus de contrôle. Les deux marchent.

### 4.1 Créer le projet Railway

1. https://railway.app → **New project** → **Deploy from GitHub repo**
2. Choisis `them311/Tee-es-t`
3. Dans **Settings** → **Source** → **Root Directory** : `studentflow`
4. Dans **Settings** → **Variables**, colle le contenu de ton `.env`
   (sans les commentaires). Au minimum :
   ```
   SUPABASE_URL
   SUPABASE_SERVICE_KEY
   FRANCE_TRAVAIL_CLIENT_ID
   FRANCE_TRAVAIL_CLIENT_SECRET
   ADZUNA_APP_ID
   ADZUNA_APP_KEY
   ADZUNA_COUNTRY
   MATCH_SCORE_THRESHOLD
   ```

### 4.2 Deux services dans le même projet

StudentFlow a besoin de **deux processus** : l'API HTTP et le worker qui
fait tourner les 3 agents en boucle. Dans Railway, clique sur **+ New** →
**GitHub Repo** une deuxième fois sur le même repo pour créer un 2ᵉ service.

| Service | Start command | Mémoire | Purpose |
|---|---|---|---|
| `studentflow-api` | `uvicorn studentflow.api:app --host 0.0.0.0 --port $PORT` | 512 MB | Reçoit les inscriptions étudiants, expose `/matches` |
| `studentflow-worker` | `python -m studentflow.cli run-agents` | 512 MB | Scraper + matcher + notifier en boucle |

Les deux services partagent exactement les mêmes variables d'environnement
(même Supabase, mêmes clés API). Railway gère les redéploiements
automatiquement à chaque `git push` sur `main`.

### 4.3 Vérifier que c'est vivant

```bash
curl https://studentflow-api.up.railway.app/health
# → {"status":"ok","version":"0.1.0"}
```

Ensuite, ouvre **Logs** du service `studentflow-worker` — tu dois voir
toutes les ~15 min :
```
Starting scraper loop (every 900s)
Running scraper france_travail
Running scraper adzuna
Running scraper hellowork
Scraper france_travail returned 50 offers
Scraper adzuna returned 50 offers
...
scraper tick: 150 items
```

---

## 5. Première inscription et premier match (1 min)

```bash
# Inscris un étudiant depuis ton terminal
curl -X POST https://studentflow-api.up.railway.app/students \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@studentflow.fr",
    "full_name": "Test User",
    "city": "Paris",
    "skills": ["react", "javascript", "python"],
    "accepted_contracts": ["apprenticeship", "internship"],
    "max_hours_per_week": 35
  }'
# → {"id": "abc-123-..."}

# Attends 1-2 min que le MatcherAgent tourne, puis :
curl https://studentflow-api.up.railway.app/students/abc-123.../matches
# → [{"offer_id": "...", "title": "...", "score": 0.87, ...}, ...]
```

Si tu vois des matches avec un score ≥ 0.6, **le système est live**.

---

## 6. Notifications (optionnel mais recommandé)

Par défaut, `NOTIFICATION_WEBHOOK_URL` est vide et le `NotifierAgent` marque
les matches comme "notifiés" sans envoyer de message réel. Pour vraiment
notifier quelqu'un :

**Option simple — Make/Zapier/n8n**
1. Crée un scénario avec un webhook comme trigger.
2. Copie l'URL du webhook dans `NOTIFICATION_WEBHOOK_URL` sur Railway.
3. Dans le scénario, branche un bloc *Send Email* ou *Send SMS* qui reçoit :
   ```json
   {
     "match_id": "...",
     "offer_id": "...",
     "student_id": "...",
     "score": 0.87,
     "reasons": ["skills chevauchent (0.75)", "même ville", ...],
     "sent_at": "2026-04-13T12:00:00"
   }
   ```
4. À toi de résoudre `student_id` → email via Supabase dans le scénario.

**Option avancée — extraction `integrations/` partagée**
Le prochain gros chantier est de sortir les modules Gmail/HubSpot/Notion
du `commercial-agent` vers un package partagé. Quand ce sera fait, le
`NotifierAgent` enverra directement des emails Gmail sans passer par un
webhook externe.

---

## 7. Observabilité et debug

| Besoin | Où regarder |
|---|---|
| Logs API | Railway → studentflow-api → Logs |
| Logs worker | Railway → studentflow-worker → Logs |
| État de la DB | Supabase → Table Editor |
| Compter les matches | Supabase → SQL Editor : `select count(*) from matches` |
| Voir les erreurs scrapers | Filtrer les logs worker sur "Scraper ... failed" |

Les 3 agents sont **isolés** : une erreur dans un scraper ne fait pas
tomber les autres, et les agents reprennent sans état via la DB — tu peux
killer et relancer le worker à tout moment sans rien perdre.

---

## 8. Ce que tu dois surveiller les premiers jours

- **Quota Adzuna** — 1000 appels/mois sur le free tier. Avec un scrape
  toutes les 15 min ça fait ~2 880/mois → **passe le `SCRAPER_INTERVAL_SECONDS`
  à 1800 (30 min)** dès que tu mets Adzuna en prod, ou upgrade le plan.
- **Qualité des matches** — si `MATCH_SCORE_THRESHOLD=0.6` crée trop de
  bruit, monte-le à 0.7 ou 0.75 en variable d'env (zéro code à changer).
- **Volumétrie DB** — Supabase free tier plafonne à 500 MB. Avec ~1k offres
  upsertées par jour, ça dure largement plusieurs mois. Prévois un cron SQL
  pour supprimer les offres >30 jours si ça gonfle.

---

## 9. Rollback en urgence

Si une release casse la prod :
1. Railway → service concerné → **Deployments** → clique sur le précédent
   déploiement vert → **Redeploy**. C'est instantané.
2. Aucune migration DB destructive n'est jamais faite par le code ;
   `schema.sql` est idempotent et jamais auto-appliqué.

---

## Récapitulatif express

```bash
# Une fois les comptes créés et les clés en main :
cp .env.example .env && vim .env
make install && make test
python -m studentflow.cli seed-demo
python -m studentflow.cli tick
# → puis push sur main, Railway déploie
```

Si tout passe vert, tu as une plateforme de matching multi-sources qui
tourne en autonomie 24/7.
