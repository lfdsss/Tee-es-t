#!/usr/bin/env bash
#
# StudentFlow — Production setup (run ONCE on your machine)
#
# This script:
#   0. Bootstraps required CLIs (Homebrew, supabase, railway) if missing
#   1. Applies the Supabase schema
#   2. Sets Railway env vars (SMTP, PUBLIC_BASE_URL)
#   3. Smoke-tests the live API
#
# Prerequisites:
#   - bash, curl, git (used by the bootstrap step)
#   - You must be logged into supabase + railway (supabase login, railway login)
#     If you skip auto-install, ensure these are on your PATH:
#       supabase CLI: brew install supabase/tap/supabase  (or npx supabase)
#       railway CLI:  npm install -g @railway/cli
#
# Usage:
#   ./setup-production.sh
#   SKIP_BOOTSTRAP=1 ./setup-production.sh   # skip step 0

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bail() { echo "❌ $*" >&2; exit 1; }
ok()   { echo "✅ $*"; }
hr()   { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

# ---- 0. Bootstrap CLIs ------------------------------------------------------
if [ "${SKIP_BOOTSTRAP:-0}" != "1" ]; then
  hr "Step 0: Bootstrap required CLIs"

  # 0a. Homebrew (used to install supabase CLI)
  if ! command -v brew >/dev/null 2>&1; then
    echo "→ Homebrew missing — running scripts/install-homebrew.sh"
    [ -x "$ROOT/scripts/install-homebrew.sh" ] \
      || bail "scripts/install-homebrew.sh missing or not executable"
    NONINTERACTIVE=1 "$ROOT/scripts/install-homebrew.sh"
    # Make brew available in this shell session
    if [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
      eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    elif [ -x /opt/homebrew/bin/brew ]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
  fi
  ok "Homebrew available: $(brew --version | head -1)"

  # 0b. Brewfile bundle — applies the curated set of CLIs in one shot
  if [ -f "$ROOT/Brewfile" ]; then
    echo "→ Running brew bundle install (Brewfile)…"
    if ! (cd "$ROOT" && brew bundle check --quiet 2>/dev/null); then
      (cd "$ROOT" && brew bundle install --quiet) \
        || echo "⚠️  brew bundle install reported issues — continuing (some deps may be optional)"
    fi
    ok "Brewfile applied"
  fi

  # 0c. Supabase CLI (defensive — should already be covered by Brewfile)
  if ! command -v supabase >/dev/null 2>&1; then
    echo "→ supabase CLI missing — installing via brew"
    brew install supabase/tap/supabase || bail "supabase install failed"
  fi
  ok "supabase CLI available: $(supabase --version 2>/dev/null || echo unknown)"

  # 0d. Railway CLI (npm-only, no brew formula)
  if ! command -v railway >/dev/null 2>&1; then
    echo "→ railway CLI missing — installing via npm"
    command -v npm >/dev/null 2>&1 || bail "npm required to install railway CLI"
    npm install -g @railway/cli || bail "railway install failed"
  fi
  ok "railway CLI available: $(railway --version 2>/dev/null || echo unknown)"
fi

# ---- 1. Supabase schema -----------------------------------------------------
hr "Step 1: Apply Supabase schema"

if ! command -v supabase >/dev/null 2>&1; then
  echo "supabase CLI not found, trying npx..."
  SUPABASE="npx supabase"
else
  SUPABASE="supabase"
fi

read -rp "Supabase project ref (from dashboard URL): " SUPA_REF
read -rp "Supabase DB password: " -s SUPA_DB_PASS
echo

echo "Applying schema.sql to project $SUPA_REF..."
$SUPABASE db push --db-url "postgresql://postgres:${SUPA_DB_PASS}@db.${SUPA_REF}.supabase.co:5432/postgres" \
  || {
    echo "⚠️  db push failed. Falling back to direct psql..."
    PGPASSWORD="$SUPA_DB_PASS" psql \
      "postgresql://postgres@db.${SUPA_REF}.supabase.co:5432/postgres" \
      -f "$ROOT/studentflow/schema.sql" \
      || bail "Could not apply schema. Please paste schema.sql manually in SQL Editor."
  }
ok "Supabase schema applied"

# ---- 2. Railway env vars ----------------------------------------------------
hr "Step 2: Configure Railway environment variables"

command -v railway >/dev/null || bail "railway CLI missing (npm install -g @railway/cli)"

echo "Setting SMTP (Brevo) + PUBLIC_BASE_URL..."
read -rp "Railway public URL [https://studentflow-api.up.railway.app]: " RAILWAY_URL
RAILWAY_URL="${RAILWAY_URL:-https://studentflow-api.up.railway.app}"

read -rp "SMTP FROM email [notifications@studentflow.fr]: " SMTP_FROM
SMTP_FROM="${SMTP_FROM:-notifications@studentflow.fr}"

read -rp "Brevo SMTP key (xsmtpsib-...): " -s BREVO_KEY
echo

read -rp "Supabase URL (https://xxx.supabase.co): " SUPA_URL
read -rp "Supabase service_role key (eyJ...): " -s SUPA_KEY
echo

railway variables set \
  SUPABASE_URL="$SUPA_URL" \
  SUPABASE_SERVICE_KEY="$SUPA_KEY" \
  SMTP_HOST=smtp-relay.brevo.com \
  SMTP_PORT=587 \
  SMTP_USERNAME="$SMTP_FROM" \
  SMTP_PASSWORD="$BREVO_KEY" \
  SMTP_FROM="$SMTP_FROM" \
  SMTP_USE_TLS=true \
  PUBLIC_BASE_URL="$RAILWAY_URL" \
  MATCH_SCORE_THRESHOLD=0.6

ok "Railway variables set"

# ---- 3. Smoke test -----------------------------------------------------------
hr "Step 3: Smoke test"

echo -n "Waiting for Railway redeploy..."
sleep 10
echo " done."

echo -n "/health: "
curl -fsS "$RAILWAY_URL/health" && echo || bail "/health failed"

echo -n "/skills/vocabulary: "
curl -fsS "$RAILWAY_URL/skills/vocabulary" | head -c 80
echo

echo -n "/stats/funnel: "
curl -fsS "$RAILWAY_URL/stats/funnel"
echo

ok "All smoke tests passed!"

hr "StudentFlow is LIVE"
echo ""
echo "  Frontend:  https://studentflow-app.netlify.app"
echo "  API:       $RAILWAY_URL"
echo "  Health:    $RAILWAY_URL/health"
echo "  Admin:     https://studentflow-app.netlify.app/admin"
echo ""
echo "Next: create a student on the web app and watch the matching magic."
