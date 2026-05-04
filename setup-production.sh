#!/usr/bin/env bash
#
# StudentFlow — Production setup (run ONCE on your machine)
#
# This script:
#   1. Applies the Supabase schema
#   2. Sets Railway env vars (SMTP, PUBLIC_BASE_URL)
#   3. Smoke-tests the live API
#
# Prerequisites:
#   - supabase CLI: brew install supabase/tap/supabase  (or npx supabase)
#   - railway CLI:  npm install -g @railway/cli
#   - You must be logged into both (supabase login, railway login)
#
# Usage:
#   ./setup-production.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bail() { echo "❌ $*" >&2; exit 1; }
ok()   { echo "✅ $*"; }
hr()   { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

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
