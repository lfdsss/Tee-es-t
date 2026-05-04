#!/bin/bash
# ─────────────────────────────────────────────
# LFDS Quiz — Déploiement Fly.io en 1 commande
# ─────────────────────────────────────────────

set -e

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   LFDS Quiz — Déploiement Fly.io         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Check flyctl
if ! command -v flyctl &> /dev/null && ! command -v fly &> /dev/null; then
    echo "  ⚠ flyctl non trouvé. Installation en cours..."
    curl -L https://fly.io/install.sh | sh
    export FLYCTL_INSTALL="/home/$USER/.fly"
    export PATH="$FLYCTL_INSTALL/bin:$PATH"
fi

FLY_CMD=$(command -v flyctl || command -v fly)
echo "  ✓ flyctl trouvé : $FLY_CMD"

# Check authentication
if ! $FLY_CMD auth whoami &> /dev/null; then
    echo "  → Connexion à Fly.io..."
    $FLY_CMD auth login
fi
echo "  ✓ Authentifié comme : $($FLY_CMD auth whoami)"

# Generate API key if .env doesn't exist
if [ ! -f .env ]; then
    API_KEY="lfds_$(openssl rand -hex 24)"
    echo "LFDS_API_KEY=$API_KEY" > .env
    echo "  ✓ Clé API générée"
else
    API_KEY=$(grep LFDS_API_KEY .env | cut -d'=' -f2)
fi

# Check if app exists
APP_NAME="lfds-quiz"
if ! $FLY_CMD apps list 2>/dev/null | grep -q "$APP_NAME"; then
    echo "  → Création de l'app Fly '$APP_NAME'..."
    $FLY_CMD launch --copy-config --no-deploy --name "$APP_NAME" --region cdg --yes
fi

# Create persistent volume if missing
if ! $FLY_CMD volumes list -a "$APP_NAME" 2>/dev/null | grep -q "quiz_data"; then
    echo "  → Création du volume persistant 'quiz_data' (1 GB)..."
    $FLY_CMD volumes create quiz_data --region cdg --size 1 -a "$APP_NAME" --yes
fi

# Set the API key as a Fly secret
echo "  → Configuration des secrets..."
$FLY_CMD secrets set LFDS_API_KEY="$API_KEY" -a "$APP_NAME"

# Deploy
echo "  → Déploiement..."
$FLY_CMD deploy -a "$APP_NAME"

# Get the URL
APP_URL="https://${APP_NAME}.fly.dev"

echo ""
echo "  ══════════════════════════════════════════"
echo "  ✅ Déploiement terminé !"
echo "  ══════════════════════════════════════════"
echo ""
echo "  🌍 URL :  $APP_URL"
echo "  🔑 Clé :  $API_KEY"
echo ""
echo "  ── Endpoints ─────────────────────────────"
echo ""
echo "  Quiz public :   $APP_URL/"
echo "  Health :        $APP_URL/api/health"
echo "  Submit :        POST $APP_URL/api/quiz/submit"
echo ""
echo "  Admin (avec x-api-key) :"
echo "    Stats :       GET $APP_URL/api/admin/stats"
echo "    CSV :         GET $APP_URL/api/admin/export/csv"
echo "    Submissions : GET $APP_URL/api/admin/submissions"
echo ""
echo "  ── Tester ───────────────────────────────"
echo ""
echo "  curl $APP_URL/api/health"
echo "  curl -H 'x-api-key: $API_KEY' $APP_URL/api/admin/stats"
echo ""
