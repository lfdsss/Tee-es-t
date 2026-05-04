# Brewfile — SNB Consulting / La Francaise Des Sauces
#
# Single source of truth for CLI tooling required across the project.
# Bootstrap a fresh machine:    brew bundle install
# Verify state:                 brew bundle check --verbose
# Remove anything not listed:   brew bundle cleanup --force
#
# Categories below are alphabetical inside each block.

# ── Core dev / git ──────────────────────────────────────────────────────────
brew "git"
brew "gh"                 # GitHub CLI — PR review, issue triage, CI tail
brew "shellcheck"         # Static analysis for the install/setup scripts
brew "jq"                 # JSON wrangling in pipelines and CRM exports
brew "yq"                 # YAML wrangling for workflows + configs
brew "ripgrep"            # Fast grep used by automation
brew "fd"                 # Fast find replacement
brew "tree"

# ── HTTP / API tooling ──────────────────────────────────────────────────────
brew "curl"
brew "httpie"             # Human-friendly HTTP client for API debugging
brew "wget"

# ── Node / JS runtime managers ──────────────────────────────────────────────
brew "node"               # Required for vite, dashboard, server/, snb-agent
brew "pnpm"

# ── Backend / DB clients ────────────────────────────────────────────────────
brew "postgresql@16"      # psql client for Supabase fallback in setup-production.sh
brew "redis"

# ── Cloud / deploy CLIs ─────────────────────────────────────────────────────
brew "supabase/tap/supabase"   # Used by setup-production.sh step 1
brew "flyctl"                  # deploy-fly.sh
brew "netlify-cli"             # netlify/ deployment

# ── Scraping / data pipelines ───────────────────────────────────────────────
brew "python@3.12"
brew "uv"                 # Fast Python package manager for scrapers/agents

# Notes:
# - Railway CLI is npm-only (no brew formula) — installed by setup-production.sh step 0c
# - Cask installs (Docker Desktop, etc.) are macOS-only and intentionally excluded
#   to keep the Brewfile portable across Linux CI runners.
