#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Homebrew — Installation reproductible (Linux/macOS)
# Source officielle : https://brew.sh/fr/
# ─────────────────────────────────────────────
#
# Usage :
#   ./scripts/install-homebrew.sh                # mode interactif standard
#   NONINTERACTIVE=1 ./scripts/install-homebrew.sh   # CI / containers
#
# Sur Linux en root, le script crée un user dédié `linuxbrew`
# (Homebrew refuse de s'exécuter en root) et expose un wrapper
# global dans /usr/local/bin/brew.

set -euo pipefail

BREW_USER="linuxbrew"
BREW_PREFIX="/home/linuxbrew/.linuxbrew"
WRAPPER="/usr/local/bin/brew"

log()  { printf "  → %s\n" "$*"; }
ok()   { printf "  ✓ %s\n" "$*"; }
fail() { printf "  ✗ %s\n" "$*" >&2; exit 1; }

# ── Prérequis ───────────────────────────────
for bin in curl git; do
  command -v "$bin" >/dev/null 2>&1 || fail "$bin requis"
done
ok "Prérequis présents (curl, git)"

OS="$(uname -s)"

# ── macOS : install standard ────────────────
if [ "$OS" = "Darwin" ]; then
  if command -v brew >/dev/null 2>&1; then
    ok "Homebrew déjà installé : $(brew --version | head -1)"
    exit 0
  fi
  log "Installation Homebrew (macOS)…"
  NONINTERACTIVE="${NONINTERACTIVE:-1}" /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ok "Homebrew installé"
  exit 0
fi

# ── Linux ───────────────────────────────────
if [ "$OS" != "Linux" ]; then
  fail "OS non supporté : $OS"
fi

# Si brew est déjà accessible, sortir
if command -v brew >/dev/null 2>&1 && brew --version >/dev/null 2>&1; then
  ok "Homebrew déjà installé : $(brew --version | head -1)"
  exit 0
fi

IS_ROOT=0
[ "$(id -u)" -eq 0 ] && IS_ROOT=1

if [ "$IS_ROOT" -eq 1 ]; then
  log "Exécution en root → création d'un user dédié '$BREW_USER'"
  if ! id "$BREW_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$BREW_USER"
    ok "User '$BREW_USER' créé"
  else
    ok "User '$BREW_USER' déjà existant"
  fi

  # Sudoers passwordless pour permettre à l'installer brew d'utiliser sudo
  if [ ! -f /etc/sudoers.d/linuxbrew ]; then
    echo "$BREW_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/linuxbrew
    chmod 0440 /etc/sudoers.d/linuxbrew
    ok "Sudoers configuré pour '$BREW_USER'"
  fi

  log "Installation Homebrew via '$BREW_USER'…"
  sudo -u "$BREW_USER" -H bash -c '
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  '

  # Wrapper global qui bascule automatiquement vers le user linuxbrew
  cat > "$WRAPPER" <<'WRAP'
#!/usr/bin/env bash
# Homebrew wrapper — route brew via le user 'linuxbrew' (root interdit par brew)
set -e
if [ "$(id -u)" -eq 0 ]; then
  exec sudo -u linuxbrew -H -- /home/linuxbrew/.linuxbrew/bin/brew "$@"
else
  exec /home/linuxbrew/.linuxbrew/bin/brew "$@"
fi
WRAP
  chmod +x "$WRAPPER"
  ok "Wrapper installé : $WRAPPER"

  # PATH persistant pour root
  if ! grep -q "brew shellenv" /root/.bashrc 2>/dev/null; then
    {
      echo ""
      echo "# Homebrew (Linuxbrew)"
      echo "eval \"\$($BREW_PREFIX/bin/brew shellenv bash)\""
    } >> /root/.bashrc
    ok "PATH ajouté à /root/.bashrc"
  fi
else
  log "Installation Homebrew (Linux, user standard)…"
  NONINTERACTIVE="${NONINTERACTIVE:-1}" /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # PATH persistant pour le user courant
  SHELL_RC="$HOME/.bashrc"
  [ -n "${ZSH_VERSION:-}" ] && SHELL_RC="$HOME/.zshrc"
  if ! grep -q "brew shellenv" "$SHELL_RC" 2>/dev/null; then
    {
      echo ""
      echo "# Homebrew (Linuxbrew)"
      echo "eval \"\$($BREW_PREFIX/bin/brew shellenv)\""
    } >> "$SHELL_RC"
    ok "PATH ajouté à $SHELL_RC"
  fi
fi

# ── Vérification ────────────────────────────
log "Vérification…"
brew --version
ok "Homebrew opérationnel — préfixe : $(brew --prefix)"

cat <<'NEXT'

  ══════════════════════════════════════════
  ✅ Homebrew installé
  ══════════════════════════════════════════

  Prochaines étapes recommandées :
    brew update
    brew install gcc           # compilateur recommandé par brew
    brew doctor                # diagnostic complet

  Doc : https://docs.brew.sh

NEXT
