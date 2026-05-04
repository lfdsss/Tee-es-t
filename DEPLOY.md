# StudentFlow — Go-live guide

This file walks through every command to take the platform from this repo to a
live, multi-tenant production deployment.

Three pieces to ship:

| Piece | What | Where |
| --- | --- | --- |
| Database | Postgres schema + RLS | Supabase |
| API + Agents | FastAPI + scraper/matcher/notifier loops | Railway (or Fly / Render) |
| Web app | Vite React SPA | Netlify |

All deployment configs are already in the repo. No code changes needed.

---

## 0. Prerequisites (5 min)

```bash
# One time: tools on your machine
brew install gh                       # GitHub CLI (or use web UI)
npm install -g @railway/cli           # Railway CLI
npm install -g netlify-cli            # Netlify CLI
```

You also need accounts (all free tiers work):

- https://supabase.com
- https://railway.app
- https://app.netlify.com (site already exists: `studentflow-app`)
- https://francetravail.io (optional — free France Travail API)
- https://developer.adzuna.com (optional — free Adzuna API)
- https://jooble.org/api/about (optional — free Jooble key)

---

## 1. Database — Supabase (3 min)

1. Create a new project at https://supabase.com → note the project URL.
2. **Project Settings → API** → copy the `service_role` key (NOT the anon key).
3. **SQL Editor → New query** → paste the full content of
   [`studentflow/schema.sql`](studentflow/schema.sql) → Run. Idempotent, safe to
   re-run.

   If you previously applied the old schema, apply the delta instead:
   [`studentflow/migrations/002_uber_grade.sql`](studentflow/migrations/002_uber_grade.sql).

4. Keep `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` handy — you'll paste them into
   Railway next.

---

## 2. API + Agents — Railway (5 min)

Railway picks up the `Dockerfile` in `studentflow/` automatically.

```bash
cd studentflow
railway login
railway init                    # create a new project
railway link                    # link current dir to the project
railway up                      # build + deploy the Docker image
```

Then in the Railway dashboard → **Variables** → paste every non-empty value from
`studentflow/.env.example`:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
FRANCE_TRAVAIL_CLIENT_ID=...
FRANCE_TRAVAIL_CLIENT_SECRET=...
ADZUNA_APP_ID=...
ADZUNA_APP_KEY=...
JOOBLE_API_KEY=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=notifications@studentflow.fr
PUBLIC_BASE_URL=https://studentflow-api.up.railway.app   # set to your actual Railway URL
```

**Start two services** in Railway (both use the same Dockerfile):

| Service | Start command |
| --- | --- |
| `api` | `uvicorn studentflow.api:app --host 0.0.0.0 --port $PORT` |
| `worker` | `python -m studentflow.cli run-agents` |

Railway's `Procfile` (already in the repo) declares both. Enable public
networking on the `api` service → note the generated URL (something like
`studentflow-api.up.railway.app`).

### Smoke test

```bash
curl https://studentflow-api.up.railway.app/health
# {"status":"ok","version":"0.2.0"}

curl https://studentflow-api.up.railway.app/skills/vocabulary | jq .skills[:5]
# ["accueil","allemand","anglais","angular","aws"]
```

---

## 3. Web app — Netlify (3 min)

Site already exists: **studentflow-app** (siteId
`75402425-a791-4c68-9dc9-64509bb6e763`).

### Option A — local one-shot deploy

```bash
cd studentflow-web
VITE_API_BASE_URL=https://studentflow-api.up.railway.app npm run build
npx netlify-cli deploy --prod --dir=dist --site=75402425-a791-4c68-9dc9-64509bb6e763
```

### Option B — link GitHub so pushes auto-deploy (recommended)

1. https://app.netlify.com/projects/studentflow-app → **Site settings → Build &
   deploy → Link repository** → pick `them311/Tee-es-t`, base `studentflow-web`,
   branch `main`.
2. **Environment variables** → set `VITE_API_BASE_URL` to the Railway URL.
   (I have pre-set it to `https://studentflow-api.up.railway.app` — update if
   your Railway URL differs.)
3. Merge your working branch to `main`. Netlify rebuilds automatically.

### Option C — GitHub Actions deploy (already configured)

`.github/workflows/deploy-web.yml` builds + deploys on every push to `main`.
Add these secrets in **Repo settings → Secrets and variables → Actions**:

| Secret | Value |
| --- | --- |
| `NETLIFY_AUTH_TOKEN` | Netlify → User settings → Applications → New access token |
| `NETLIFY_SITE_ID` | `75402425-a791-4c68-9dc9-64509bb6e763` |

And repo variable `VITE_API_URL` with the Railway URL (or it falls back to the
hardcoded default).

---

## 4. Post-deploy wiring

1. Update `PUBLIC_BASE_URL` on Railway to the **exact** Railway URL you got.
   This URL is used to build the accept/decline links embedded in every
   notification email. Mismatched → clickable links 404.

2. Update `VITE_API_BASE_URL` on Netlify to the **exact** Railway URL. Rebuild.

3. In the Netlify dashboard → **Redirects** — the `_redirects` file is already
   in `studentflow-web/public/` (served by Vite). SPA routes work out of the
   box.

---

## 5. Verify end-to-end

```bash
# 1. API is up
curl -s https://studentflow-api.up.railway.app/health

# 2. Web app loads
open https://studentflow-app.netlify.app

# 3. Create a student from the web app → you should see cold-start matches
#    on the /matches/:id page immediately (empty inbox only if no offers yet).

# 4. Trigger one scraper tick to populate offers
railway run python -m studentflow.cli tick
# Look for "Scraper tick: N offers upserted" in the log.

# 5. Refresh /matches/:id — the inbox should fill.
```

---

## 6. Local development

```bash
# Backend
cd studentflow
cp .env.example .env            # then fill what you care about
pip install -e ".[dev]"
python -m studentflow.cli run-api   # http://localhost:8000

# Frontend (in another terminal)
cd studentflow-web
npm install
npm run dev                     # http://localhost:5173
```

Or everything at once with `docker compose`:

```bash
docker compose up --build
# API on :8000, Vite dev server on :5173, agents running in background
```

---

## 7. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Accept/decline links 404 in emails | `PUBLIC_BASE_URL` on Railway doesn't match the deployed URL |
| Frontend CORS error | Check that the Netlify site is calling the Railway URL (env var), not localhost |
| Matches empty forever | Either no offers (`studentflow tick` to force a scrape) or `MATCH_SCORE_THRESHOLD` too high |
| Notifications not sending | `SMTP_*` incomplete → falls back to webhook → falls back to null. Check the `/stats` endpoint |
| SSE stream disconnects | Some proxies strip `text/event-stream` — Railway and Netlify both support it natively |
| Indeed scraper returns 0 | Indeed throttles RSS by region. Other 4 sources keep delivering offers |

---

## 8. What's missing / next steps

- **Authentication**: every endpoint is open. Add Supabase Auth or a simple API
  key before going beyond private beta.
- **Admin RBAC**: `/admin` dashboard is public. Gate it.
- **Scaling**: `realtime.py` uses in-memory pub/sub. Single-process only. Swap
  for Redis pub/sub (drop-in) before running multiple API workers.
- **Rate limits**: add `slowapi` middleware on public POST endpoints.
