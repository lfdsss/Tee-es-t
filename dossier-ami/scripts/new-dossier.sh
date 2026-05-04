#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# new-dossier.sh — orchestre le déploiement d'un dossier en 1 commande.
#
# Usage :
#   ./new-dossier.sh <slug>            # bootstrap (copie profil.json + ouvre l'éditeur)
#   ./new-dossier.sh <slug> --build    # regénère les courriers + PDFs après édition
#   ./new-dossier.sh <slug> --status   # affiche l'état du dossier (marqueurs restants)
#   ./new-dossier.sh <slug> --open     # ouvre le dossier PDF dans le file manager
#
# Exemple :
#   ./new-dossier.sh marie-l           # crée dossier-ami/exemples/marie-l/
#   $EDITOR dossier-ami/exemples/marie-l/profil.json
#   ./new-dossier.sh marie-l --build   # → pdf/*.pdf prêts à imprimer
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXEMPLES="$ROOT/exemples"
TEMPLATE_PROFILE="$EXEMPLES/sophie-dupont/profil.json"
PERSONALIZE="$ROOT/scripts/personalize.py"

bail() { echo "❌ $*" >&2; exit 1; }
ok()   { echo "✓ $*"; }
hr()   { printf '\n\033[1m── %s ──\033[0m\n' "$*"; }

usage() {
  sed -n '4,15p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
  exit 0
}

[ $# -ge 1 ] || usage
[ "$1" = "-h" ] || [ "$1" = "--help" ] && usage

SLUG="$1"
ACTION="${2:-bootstrap}"

# Validation du slug : lettres, chiffres, tirets uniquement
[[ "$SLUG" =~ ^[a-z0-9-]+$ ]] || bail "slug invalide : '$SLUG' (autorisé : a-z 0-9 -)"
[ "$SLUG" != "sophie-dupont" ] || bail "slug 'sophie-dupont' réservé à l'exemple public — choisis autre chose"

DOSSIER="$EXEMPLES/$SLUG"
PROFILE="$DOSSIER/profil.json"

case "$ACTION" in

  bootstrap|"")
    [ -f "$TEMPLATE_PROFILE" ] || bail "template introuvable : $TEMPLATE_PROFILE"
    if [ -f "$PROFILE" ]; then
      ok "profil existant : $PROFILE"
    else
      mkdir -p "$DOSSIER"
      cp "$TEMPLATE_PROFILE" "$PROFILE"
      ok "profil créé : $PROFILE (copie de sophie-dupont)"
    fi

    hr "Étape suivante"
    echo "  1. Édite le profil avec les vraies infos :"
    echo "       \$EDITOR $PROFILE"
    echo
    echo "  2. Génère les courriers + PDFs :"
    echo "       $0 $SLUG --build"
    echo
    echo "  Le dossier $DOSSIER est exclu du dépôt git (.gitignore)."
    ;;

  --build|build)
    [ -f "$PROFILE" ] || bail "profil introuvable : $PROFILE — lance d'abord '$0 $SLUG'"
    [ -f "$PERSONALIZE" ] || bail "personalize.py introuvable"

    hr "Génération du dossier $SLUG"
    python3 "$PERSONALIZE" "$PROFILE"

    # Vérifie qu'aucun marqueur ne traîne
    LEFT=$(grep -rc "À ADAPTER\|À COMPLÉTER" "$DOSSIER/courriers/" 2>/dev/null \
           | awk -F: '{s+=$NF} END {print s+0}')
    if [ "$LEFT" -gt 0 ]; then
      hr "⚠ Marqueurs restants ($LEFT)"
      grep -rn "À ADAPTER\|À COMPLÉTER" "$DOSSIER/courriers/" | head -10
      echo
      echo "  → édite $PROFILE pour les compléter, puis relance --build"
      exit 1
    fi

    ok "Dossier prêt : $DOSSIER/pdf/"
    ls -1 "$DOSSIER/pdf/" 2>/dev/null | sed 's/^/    /'
    ;;

  --status|status)
    [ -f "$PROFILE" ] || bail "profil introuvable : $PROFILE"

    hr "État du dossier $SLUG"
    echo "  Profil   : $PROFILE"
    [ -d "$DOSSIER/courriers" ] && \
      echo "  Courriers: $(find "$DOSSIER/courriers" -name '*.md' | wc -l) markdown" \
      || echo "  Courriers: (pas encore générés — lance --build)"
    [ -d "$DOSSIER/pdf" ] && \
      echo "  PDFs     : $(find "$DOSSIER/pdf" -name '*.pdf' | wc -l) PDFs ($(du -sh "$DOSSIER/pdf" 2>/dev/null | cut -f1))" \
      || echo "  PDFs     : (pas encore générés — lance --build)"

    if [ -d "$DOSSIER/courriers" ]; then
      LEFT=$(grep -rl "À ADAPTER\|À COMPLÉTER" "$DOSSIER/courriers/" 2>/dev/null | wc -l)
      if [ "$LEFT" -gt 0 ]; then
        echo "  ⚠ Marqueurs restants dans $LEFT fichier(s)"
      else
        echo "  ✓ Aucun marqueur restant — dossier envoyable"
      fi
    fi
    ;;

  --open|open)
    [ -d "$DOSSIER/pdf" ] || bail "PDFs non générés — lance d'abord '$0 $SLUG --build'"
    if command -v xdg-open &>/dev/null; then
      xdg-open "$DOSSIER/pdf/"
    elif command -v open &>/dev/null; then
      open "$DOSSIER/pdf/"
    else
      echo "  Dossier : $DOSSIER/pdf/"
      ls -1 "$DOSSIER/pdf/"
    fi
    ;;

  *)
    bail "action inconnue : $ACTION (utilise --build, --status, --open, ou rien)"
    ;;
esac
