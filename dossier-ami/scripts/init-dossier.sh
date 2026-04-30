#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# init-dossier.sh
#
# Génère une copie propre et vierge du kit "dossier-ami" dans un dossier cible.
# Les templates de courriers, la checklist, le suivi et les prompts sont copiés.
# Les sous-dossiers de pièces et d'archives sont créés vides (avec un .gitkeep
# et un README rappelant la confidentialité).
#
# Usage :
#   ./init-dossier.sh <chemin/cible>
#   ./init-dossier.sh ~/dossiers/dupont-2026
#
# Le script est idempotent : relancer ne supprime jamais les fichiers déjà
# personnalisés par l'utilisateur. Il n'écrase un fichier existant que si
# --force est passé.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: init-dossier.sh <cible> [--force]

  <cible>   Chemin du dossier à créer (sera créé s'il n'existe pas).
  --force   Écrase les fichiers existants par les templates frais.

Exemple :
  ./init-dossier.sh ~/dossiers/dupont-2026
EOF
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

TARGET="$1"
FORCE=false
if [[ "${2:-}" == "--force" ]]; then
  FORCE=true
fi

# Source = dossier-ami racine (parent du dossier scripts/)
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -d "$SOURCE/courriers" ]]; then
  echo "❌ Source kit not found at $SOURCE — script must live in dossier-ami/scripts/" >&2
  exit 1
fi

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

echo "→ Source : $SOURCE"
echo "→ Cible  : $TARGET"
echo

# ── 1. Copie des templates et fichiers de pilotage ──────────────────────────
copy_file() {
  local rel="$1"
  local src="$SOURCE/$rel"
  local dst="$TARGET/$rel"

  mkdir -p "$(dirname "$dst")"

  if [[ -f "$dst" && "$FORCE" != true ]]; then
    echo "  ⏭  (existe) $rel"
    return
  fi
  cp "$src" "$dst"
  echo "  ✓ $rel"
}

echo "── Templates de courriers ──"
while IFS= read -r f; do
  rel="${f#$SOURCE/}"
  copy_file "$rel"
done < <(find "$SOURCE/courriers" -type f -name '*.md')

echo
echo "── Pilotage (README, checklist, suivi, prompts) ──"
for f in README.md CHECKLIST.md SUIVI.md SUIVI.csv prompts/claude-code.md; do
  if [[ -f "$SOURCE/$f" ]]; then
    copy_file "$f"
  fi
done

# ── 2. Sous-dossiers vides pour les pièces et archives ──────────────────────
echo
echo "── Sous-dossiers de pièces (vides) ──"
for sub in identite contrats releves correspondances preuves; do
  d="$TARGET/pieces/$sub"
  mkdir -p "$d"
  touch "$d/.gitkeep"
  echo "  ✓ pieces/$sub/"
done

mkdir -p "$TARGET/archives/recus-envois"
touch "$TARGET/archives/recus-envois/.gitkeep"
echo "  ✓ archives/recus-envois/"

# ── 3. README local de confidentialité ──────────────────────────────────────
cat > "$TARGET/pieces/README.md" <<'EOF'
# Pièces du dossier — confidentielles

Ce dossier contient des données personnelles. **Ne pas pousser dans un dépôt
public.** Le `.gitignore` du kit exclut ce dossier de tout commit.

Sous-dossiers :
- `identite/`        — pièce d'identité, justificatif de domicile, RIB
- `contrats/`        — contrats signés, conditions générales et particulières
- `releves/`         — relevés bancaires, factures, échéanciers
- `correspondances/` — emails, courriers, captures de messagerie sécurisée
- `preuves/`         — captures, photos, attestations, PV

Préfixe les fichiers numériquement (`01-cni.pdf`, `02-justif.pdf`...) pour
qu'ils ressortent dans l'ordre voulu une fois imprimés.
EOF

# ── 4. .gitignore local pour protéger les données ───────────────────────────
cat > "$TARGET/.gitignore" <<'EOF'
# Données personnelles — ne JAMAIS committer
pieces/**/*
!pieces/**/.gitkeep
!pieces/README.md
archives/**/*
!archives/**/.gitkeep

# Outputs générés
*.pdf
INDEX.pdf

# OS
.DS_Store
Thumbs.db
EOF
echo "  ✓ .gitignore (protège pieces/ et archives/)"

# ── 5. Récap ────────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════════════"
echo "  ✅ Dossier initialisé"
echo "════════════════════════════════════════════════════════"
echo
echo "  Cible : $TARGET"
echo
echo "  Étapes suivantes :"
echo "    1. cd \"$TARGET\""
echo "    2. Remplir les variables {…} dans courriers/<organisme>/*.md"
echo "       (ou utiliser le prompt Claude Code dans prompts/claude-code.md)"
echo "    3. Déposer les pièces dans pieces/<sous-dossier>/"
echo "    4. Tenir SUIVI.md à jour à chaque envoi"
echo
