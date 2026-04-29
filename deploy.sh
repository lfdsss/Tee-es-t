#!/usr/bin/env bash
#
# StudentFlow — one-shot deploy helper.
#
# Usage:
#   ./deploy.sh web           # build + deploy frontend to Netlify
#   ./deploy.sh api           # build + deploy API to Railway
#   ./deploy.sh all           # both
#   ./deploy.sh smoke URL     # smoke-test a live API URL
#
# Requires:
#   - netlify-cli  (npm install -g netlify-cli)
#   - railway      (npm install -g @railway/cli)
#   - You must be logged into both (`netlify login`, `railway login`)
#
# Env vars (optional):
#   VITE_API_BASE_URL   API URL baked into the frontend build.
#                       Defaults to https://studentflow-api.up.railway.app
#   NETLIFY_SITE_ID     Netlify site id.
#                       Defaults to the studentflow-app site.

set -euo pipefail

NETLIFY_SITE_ID="${NETLIFY_SITE_ID:-75402425-a791-4c68-9dc9-64509bb6e763}"
API_URL_DEFAULT="https://studentflow-api.up.railway.app"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-$API_URL_DEFAULT}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bail() { echo "❌ $*" >&2; exit 1; }
hr() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

deploy_web() {
  hr "Build + deploy frontend → Netlify"
  command -v netlify >/dev/null || bail "netlify-cli missing (npm install -g netlify-cli)"
  cd "$ROOT/studentflow-web"
  echo "VITE_API_BASE_URL=$VITE_API_BASE_URL"
  npm ci
  npm test -- --run
  VITE_API_BASE_URL="$VITE_API_BASE_URL" npm run build
  netlify deploy --prod --dir=dist --site="$NETLIFY_SITE_ID"
  echo "✓ Web deployed: https://studentflow-app.netlify.app"
}

deploy_api() {
  hr "Build + deploy API → Railway"
  command -v railway >/dev/null || bail "railway CLI missing (npm install -g @railway/cli)"
  cd "$ROOT/studentflow"
  python -m pytest -q
  railway up
  echo "✓ API deployed. Find the URL in the Railway dashboard."
}

smoke() {
  local url="${1:-}"
  [ -n "$url" ] || bail "usage: ./deploy.sh smoke https://your-api.example.com"
  hr "Smoke-testing $url"

  echo -n "/health: "
  curl -fsS "$url/health" || bail "FAIL"
  echo

  echo -n "/skills/vocabulary: "
  curl -fsS "$url/skills/vocabulary" | head -c 80
  echo

  echo -n "/stats/funnel: "
  curl -fsS "$url/stats/funnel"
  echo

  echo "✓ Smoke OK"
}

case "${1:-}" in
  web)   deploy_web ;;
  api)   deploy_api ;;
  all)   deploy_api && deploy_web ;;
  smoke) smoke "${2:-}" ;;
  *)
    echo "Usage: $0 {web|api|all|smoke URL}"
    exit 1
    ;;
esac
