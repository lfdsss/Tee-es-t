#!/bin/bash
# ─────────────────────────────────────────────
# LFDS Quiz — Setup automatique
# ─────────────────────────────────────────────

set -e

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   LFDS Quiz — Installation               ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "  ❌ Node.js non trouvé. Installez Node.js 18+ : https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "  ❌ Node.js $NODE_VERSION détecté. Version 18+ requise."
    exit 1
fi
echo "  ✓ Node.js $(node -v) détecté"

# Install dependencies
echo "  → Installation des dépendances..."
npm install --silent
echo "  ✓ Dépendances installées"

# Generate .env if missing
if [ ! -f .env ]; then
    API_KEY="lfds_$(openssl rand -hex 24)"
    echo "LFDS_API_KEY=$API_KEY" > .env
    echo "PORT=3001" >> .env
    echo "  ✓ Clé API générée et sauvegardée dans .env"
else
    API_KEY=$(grep LFDS_API_KEY .env | cut -d'=' -f2)
    echo "  ✓ .env existant détecté"
fi

# Create data directory
mkdir -p server/data
echo "  ✓ Dossier de données créé"

# Build frontend
echo "  → Build du frontend..."
npx vite build --silent 2>/dev/null || npx vite build
echo "  ✓ Frontend compilé dans dist/"

echo ""
echo "  ══════════════════════════════════════════"
echo "  ✅ Installation terminée !"
echo "  ══════════════════════════════════════════"
echo ""
echo "  Ta clé API : $API_KEY"
echo ""
echo "  ── Commandes ──────────────────────────────"
echo ""
echo "  Développement (2 terminaux) :"
echo "    npm run dev:server    → API sur :3001"
echo "    npm run dev:front     → Front sur :3000"
echo ""
echo "  Ou tout en un :"
echo "    npm run dev"
echo ""
echo "  Production :"
echo "    npm run start         → Build + serve sur :3001"
echo ""
echo "  Docker :"
echo "    docker compose up -d  → Tout en un conteneur"
echo ""
echo "  ── Accès admin ────────────────────────────"
echo ""
echo "  Stats :  curl -H 'x-api-key: $API_KEY' http://localhost:3001/api/admin/stats"
echo "  CSV :    curl -H 'x-api-key: $API_KEY' http://localhost:3001/api/admin/export/csv -o data.csv"
echo ""
