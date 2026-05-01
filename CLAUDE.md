# CLAUDE.md — Tee-es-t monorepo

Operational map for AI assistants working in this repository. The repo bundles
several SNB Consulting systems plus the LFDS side-project under one Git tree.
Each sub-project is self-contained with its own runbook, deploy target, and
(when warranted) its own `CLAUDE.md`. Read this file first to orient, then
read the sub-project doc before touching code there.

> **Per-subproject `CLAUDE.md` files override this one for their scope.**
> Notably: [`studentflow/CLAUDE.md`](./studentflow/CLAUDE.md).

---

## Operating posture (condensed)

You are a senior autonomous engineer + product builder + business operator.
You design, build, refactor and connect systems that produce real operational
value. You are not a passive assistant.

Optimize, in order:

1. **Business value** — every technical choice must serve a real operational,
   commercial, or strategic outcome.
2. **Working systems > theoretical perfection** — robust, modular, deployable
   beats elegant abstractions.
3. **Simplicity before sophistication** — no complexity without measurable benefit.
4. **Modular by default** — features must be extendable, replaceable, composable.
5. **Ship fast, iterate** — assume the project evolves quickly.
6. **Proactive optimization** — flag weak structure, dead code, missing modules,
   automation opportunities. Don't only execute; improve.

Avoid: premature abstractions, demo-only code pretending to be production, fragmented
files without benefit, undocumented assumptions, dependencies without justification.

**Default response shape after a substantial change:**

1. What was implemented
2. Why it matters operationally
3. What is still missing
4. What should be improved next
5. Business impact
6. Automation opportunities unlocked

When in doubt about how to behave, default to:
> *"Refactor and extend this repository into a clean, modular, deployable,
> automation-oriented system aligned with real operational and business
> outcomes. Identify missing modules, improve architecture, and prioritize
> high-impact implementations."*

---

## Repository map

| Path                  | Stack                          | Business role                                                | Status         | Deploy target              |
| --------------------- | ------------------------------ | ------------------------------------------------------------ | -------------- | -------------------------- |
| `commercial-agent/`   | Python 3.12 + Claude Agent SDK | Autonomous sales robot (Gmail · HubSpot · Notion · GitHub)   | **Production** | GitHub Actions cron        |
| `studentflow/`        | Python 3.11 + FastAPI          | Real-time student-job marketplace (scraper/matcher/notifier) | **MVP**        | Railway (API + worker)     |
| `studentflow-web/`    | Vite + React + TypeScript      | StudentFlow front-end SPA                                    | **MVP**        | Netlify (`studentflow-app`)|
| `src/` + `server/` + `netlify/functions/` | React 18 + Vite + Express + Netlify Blobs | LFDS Quiz — lead-gen quiz pushing to HubSpot | **Production** | Netlify + Fly.io (`lfds-quiz`) |
| `docs/`               | Static HTML + JSON             | Public status page + portfolio (bot-owned `status.json`)     | Production     | Netlify                    |
| `archive/`            | Static HTML                    | Legacy / one-shot artifacts kept for reference               | **Archive**    | —                          |

Top-level config files: `package.json` (LFDS Quiz, name `lfds-quiz`), `vite.config.js`,
`Dockerfile`, `docker-compose.yml`, `netlify.toml`, `fly.toml`, plus the helper
scripts `setup.sh`, `setup-production.sh`, `deploy.sh`, `deploy-fly.sh`.

---

## Sub-project runbooks

### 1. Commercial Robot — `commercial-agent/`

Autonomous Python agent driving the SNB Consulting commercial pipeline.

**Entry points**
- `main.py` — interactive REPL around the agent loop
- `autonomous.py <routine>` — non-interactive cron entry (used by GitHub Actions)
- `agent_loop.py` — shared agent loop (tool-use over Anthropic API)
- `update_status.py <routine>` — writes `docs/status.json` and `docs/missions/`

**Key modules**
- `config/system_prompt.py` — agent persona / instructions
- `config/routines.py` — `morning`, `followup`, `weekly_audit` definitions
- `tools/` — `gmail.py`, `hubspot.py`, `notion.py`, `github_tools.py`,
  `livrables.py`, `http_utils.py`
- `tests/test_smoke.py` — smoke coverage

**Run locally**
```bash
cd commercial-agent
pip install -r requirements.txt
cp .env.example .env            # fill ANTHROPIC, HUBSPOT, GMAIL, NOTION keys
python main.py                  # interactive
python autonomous.py morning    # one-shot routine
```

**Deploy** — runs on `ubuntu-latest` in GitHub Actions every 10 minutes
(see `.github/workflows/robot.yml`). No dedicated server. Routine selection is
inferred from Paris-time hour-of-day / day-of-week, or overridden via
`workflow_dispatch`. Results are committed back to `main` as
`Robot: mise a jour statut (<routine>)`.

**Read also** — `commercial-agent/README.md`.

---

### 2. StudentFlow API + agents — `studentflow/`

Real-time matching engine ("Uber for student jobs"). Three agent loops
(scraper / matcher / notifier) over a Supabase Postgres backend, exposed via
FastAPI.

**Entry points**
- `src/studentflow/api.py` — FastAPI app
- `src/studentflow/cli.py` — CLI: `studentflow run-api`, `run-agents`, `tick`
- `src/studentflow/agents.py` — `ScraperAgent` (15 min) · `MatcherAgent` (1 min) · `NotifierAgent` (30 s)
- `src/studentflow/matching.py` — pure deterministic scorer (no I/O)
- `src/studentflow/scrapers/` — live: `france_travail` (REST), `adzuna` and `jooble` (REST + API key), `hellowork` and `indeed` (RSS). Stubs: `studentjob` (HTML, blocked on Cloudflare-style anti-bot from sandbox/CI), `jobteaser` (per-school OAuth credentials). Shared text helpers in `scrapers/_text.py` (contract guessing, city extraction, HTML stripping)
- `schema.sql` — full Postgres schema (idempotent)
- `migrations/002_uber_grade.sql` — delta if you previously applied an older schema

**Run locally**
```bash
cd studentflow
make install        # pip install -e ".[dev]"
make test           # pytest (23/23 passing)
make test-cov       # pytest + coverage
make lint           # ruff check
make format         # ruff format
make run-api        # uvicorn on :8000
make run-agents     # the 3 loops
```

Falls back to an in-memory repo when `SUPABASE_URL` is unset — `make run-api`
boots with zero external services.

**Deploy** — Railway picks up `studentflow/Dockerfile` automatically.
`Procfile` declares two services: `api` (`uvicorn studentflow.api:app`) and
`worker` (`python -m studentflow.cli run-agents`). Postgres lives in Supabase.
Full procedure in [`DEPLOY.md`](./DEPLOY.md).

**Read also** — [`studentflow/CLAUDE.md`](./studentflow/CLAUDE.md) for the
matching-engine contract, agent isolation rules, and scoring critère extension
recipe. **Do not duplicate or contradict that file from here.**

---

### 3. StudentFlow Web — `studentflow-web/`

Vite + React 18 + TypeScript SPA for students and admins.

**Entry points**
- `src/main.tsx` → `src/App.tsx`
- `src/api.ts` — typed HTTP layer against the Railway API
- `src/pages/` — routed views
- `src/test-setup.ts` — Vitest setup

**Run locally**
```bash
cd studentflow-web
npm install
npm run dev         # Vite on :5173
npm run build       # production bundle in dist/
npm run preview     # serve the build locally
```

Set `VITE_API_BASE_URL` to the Railway URL (defaults baked in for prod).

**Deploy** — Netlify site `studentflow-app`
(siteId `75402425-a791-4c68-9dc9-64509bb6e763`). Either link the repo for
auto-deploy, or use the GitHub Action `.github/workflows/deploy-web.yml`
(needs secrets `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID`).

---

### 4. LFDS Quiz — root `src/` + `server/` + `netlify/functions/`

Consumer lead-gen quiz for La Française des Sauces. Same source code,
two deployment shapes (Netlify static + Fly.io container).

**Entry points**
- `index.html` → `src/main.jsx` → `src/components/QuizApp.jsx`
- `src/data/quizData.js` — questions and scoring
- `src/hooks/useQuizEngine.js` — quiz state machine
- `server/index.js` — Express API on port 3001
- `server/hubspot.js` — fire-and-forget lead push to HubSpot
- `netlify/functions/{health,quiz-submit,admin-stats,admin-export}.js` —
  serverless equivalents using Netlify Blobs as KV store

**API surface** (Express)
- `POST /api/quiz/submit` — public, stores JSON + appends to daily JSONL,
  triggers HubSpot push
- `GET /api/admin/submissions|stats|export/csv` — `x-api-key` required
- `DELETE /api/admin/submissions/:sessionId` — `x-api-key` required
- `GET /api/health` — public

**Run locally**
```bash
npm install
npm run dev         # Vite on :3000 + Express on :3001 (via concurrently)
npm run dev:front   # Vite alone
npm run dev:server  # Express alone
npm run build       # Vite build (defaults to docs/quiz/)
npm run start       # build + serve via Express on :3001
```

API key is auto-generated into `.env` on first run if `LFDS_API_KEY` is empty.

**Deploy**
- **Netlify** — `netlify.toml` publishes `docs/`, functions auto-bundled with
  esbuild. Vite output goes to `docs/quiz/` under base `/quiz/`.
- **Fly.io** — `fly.toml` (app `lfds-quiz`, region `cdg`). `Dockerfile` builds
  the SPA with `VITE_BASE=/` and `VITE_OUT_DIR=dist`, then serves via Express
  on port 3001. Persistent volume `quiz_data` mounts at `/app/server/data`.
  One-shot deploy: `./deploy-fly.sh`.

---

## CI & automation — `.github/workflows/`

| Workflow                       | Trigger                                                  | Purpose                                                 |
| ------------------------------ | -------------------------------------------------------- | ------------------------------------------------------- |
| `robot.yml`                    | cron `*/10 * * * *` + `workflow_dispatch`                | Run commercial robot routine, commit `docs/status.json` |
| `commercial-agent-ci.yml`      | push/PR touching `commercial-agent/**`                   | pytest smoke tests                                      |
| `studentflow-ci.yml`           | push/PR touching `studentflow/**`                        | ruff + pytest                                           |
| `studentflow-web-ci.yml`       | push/PR touching `studentflow-web/**`                    | Vite build + Vitest                                     |
| `lfds-quiz-ci.yml`             | push/PR touching `src/`, `server/`, `netlify/functions/` | Vite build + Express health smoke                       |
| `deploy-api.yml`               | push to `main` (studentflow path) / dispatch             | Deploy StudentFlow API to Railway                       |
| `deploy-web.yml`               | push to `main` (studentflow-web path) / dispatch         | Deploy StudentFlow web to Netlify                       |
| `configure-railway.yml`        | dispatch                                                 | Sync Railway env vars                                   |
| `netlify-deploy.yml`           | push to `main` / dispatch                                | Deploy `docs/` to Netlify                               |
| `mission-response.yml`         | scheduled                                                | Mission auto-responder for the commercial robot         |

**`robot.yml` specifics** (most active workflow — ~30 commits/day):
- Cron every 10 minutes, plus manual dispatch with routine choice.
- Smart routine selection in Paris time:
  `Friday ≥ 16:00 → weekly_audit`, `hour < 12 → morning`, else `followup`.
- After running, the workflow rebases on `origin/main` and pushes
  `docs/status.json` (+ `docs/missions/`) with up to 4 retries
  to handle concurrent cron runs.
- Bot identity: `Robot Commercial <robot@snbbm-consulting.com>`.
- Commit message pattern: `Robot: mise a jour statut (<routine>)`.

---

## Conventions

### Branches
- `main` — protected, deployable.
- `claude/<slug>` — branches for Claude-Code-driven work
  (current: `claude/add-claude-documentation-zlT9w`).
- Push with `git push -u origin <branch>`. On network failure, retry up to 4
  times with exponential backoff (2s · 4s · 8s · 16s).
- **Do not push to `main` directly** unless explicitly authorized.

### Commits
- Conventional prefixes for human commits:
  `feat:` · `fix:` · `refactor:` · `docs:` · `ci:` · `chore:` · `test:`.
- **Robot commits** use `Robot: mise a jour statut (<routine>)` — leave them
  alone, do not amend or rebase them.

### Python (`commercial-agent/`, `studentflow/`)
- 3.11+ (commercial-agent CI uses 3.12).
- Type hints everywhere.
- Pydantic v2 for models.
- `ruff` for lint and format (StudentFlow only — required by CI).
- `pytest` for tests; StudentFlow targets >90% coverage on `matching.py`.
- Package via `pyproject.toml` (StudentFlow) or `requirements.txt` (commercial-agent).

### JavaScript / TypeScript
- Node ≥ 18.
- Vite for bundling (LFDS Quiz on Vite 6 + JS, StudentFlow web on Vite + TS strict).
- Express 4 for the LFDS API.
- No enforced linter at the root JS project — keep it simple, no premature ESLint config.

### Secrets
- **Never commit `.env`.** Each sub-project ships an `.env.example` — copy and fill.
- Production secrets live in:
  - GitHub Actions → robot + StudentFlow CI
  - Railway dashboard → StudentFlow API/worker
  - Netlify dashboard → StudentFlow web + LFDS docs/quiz
  - Fly.io secrets → LFDS Quiz container

### Status surface
- `docs/status.json`, `docs/missions/`, `docs/livrables.html`, `docs/documents/`
  are **bot-owned**. Don't hand-edit. If you need to change shape, update the
  generator (`commercial-agent/update_status.py` or `commercial-agent/tools/livrables.py`)
  rather than the artifacts.
- `docs/index.html` and the other static pages are human-owned — fair game.

---

## Key files index

**Business logic**
- `commercial-agent/config/system_prompt.py` — agent persona
- `commercial-agent/config/routines.py` — morning / followup / weekly_audit
- `studentflow/src/studentflow/matching.py` — scoring algorithm (pure)

**Data models / schema**
- `studentflow/src/studentflow/models.py` — Pydantic schemas
- `studentflow/schema.sql` — Postgres tables (offers · students · matches · notifications)
- `studentflow/migrations/002_uber_grade.sql` — schema delta

**Integrations**
- `server/hubspot.js` — LFDS Quiz → HubSpot
- `commercial-agent/tools/{gmail,hubspot,notion,github_tools,livrables}.py`
- `studentflow/src/studentflow/scrapers/*.py`
- `studentflow/src/studentflow/notifiers/*.py`

**CI & deploy**
- `.github/workflows/robot.yml` — cron + smart routine selection + rebase-retry push
- `.github/workflows/studentflow-ci.yml` · `studentflow-web-ci.yml` · `commercial-agent-ci.yml` · `lfds-quiz-ci.yml`
- `Dockerfile` (LFDS) · `studentflow/Dockerfile`
- `fly.toml` · `netlify.toml` · `studentflow-web/netlify.toml` · `studentflow/railway.toml`
- `docker-compose.yml` — full local stack
- `deploy.sh` · `deploy-fly.sh` · `setup.sh` · `setup-production.sh`

**Entry points**
- `src/main.jsx` · `server/index.js` (LFDS Quiz)
- `commercial-agent/main.py` · `commercial-agent/autonomous.py`
- `studentflow/src/studentflow/cli.py` · `studentflow/src/studentflow/api.py`
- `studentflow-web/src/main.tsx`

**Reading order for a new task**
1. This file (you are here).
2. The relevant sub-project `README.md`.
3. The relevant sub-project `CLAUDE.md` if one exists.
4. `DEPLOY.md` if the change touches deployment.

---

## When working in this repo

1. **Identify the sub-project first.** Don't assume the whole repo is one app —
   it isn't. Stack and conventions vary.
2. **Read the sub-project's `CLAUDE.md` / `README.md` before editing.** The
   StudentFlow doc in particular contains hard contracts (matching engine purity,
   scraper isolation, DB-as-truth) that must not be broken.
3. **Run that sub-project's tests locally** (`make test`, `pytest`, `npm test`)
   before pushing. CI will block otherwise.
4. **Follow the deploy story of the sub-project you changed.** Don't introduce a
   new deploy target; reuse what's there.
5. **Don't hand-edit bot-owned files** (`docs/status.json`, `docs/missions/`,
   `docs/livrables.html`, `docs/documents/`). Modify the generator instead.
6. **Default to a `claude/<slug>` branch.** Conventional commit prefix.
7. **Apply the operating posture** — when finishing, summarize what shipped,
   why it matters, what's missing, what's next, business impact, and the
   automation opportunities the change unlocks.
