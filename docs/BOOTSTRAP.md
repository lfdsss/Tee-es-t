# Bootstrap

How to bring a fresh machine (laptop, VM, CI runner) up to a working state for this repo.

## TL;DR

```bash
git clone https://github.com/them311/Tee-es-t.git
cd Tee-es-t
make bootstrap
```

That's it. The command is idempotent — re-running it is safe and fast.

## What `make bootstrap` does

1. **Installs Homebrew** (Linux or macOS) if missing, via `scripts/install-homebrew.sh`.
   - On Linux running as root, creates a dedicated `linuxbrew` user (Homebrew refuses to run as root) and exposes a wrapper at `/usr/local/bin/brew` that transparently routes commands through that user.
   - Persists `brew shellenv` in `~/.bashrc` (or `~/.zshrc`).
2. **Applies the Brewfile** via `brew bundle install` — installs the curated CLI tooling pinned by the project.

Prerequisites: only `bash`, `curl`, and `git`.

## Targets

| Target              | Effect |
|---------------------|--------|
| `make help`         | List all targets |
| `make bootstrap`    | Full bootstrap (Homebrew + Brewfile) |
| `make brew`         | Install Homebrew only |
| `make brewfile`     | Apply Brewfile only (assumes brew is present) |
| `make check`        | Diff Brewfile vs installed packages |
| `make clean-brew`   | Remove anything not listed in Brewfile (DESTRUCTIVE — prompts) |
| `make lint`         | Shellcheck the bootstrap scripts |
| `make doctor`       | Run `brew doctor` |
| `make setup-prod`   | Run `setup-production.sh` (StudentFlow API + Railway + Supabase) |
| `make install`      | `npm install` for the LFDS quiz |
| `make dev`          | `npm run dev` (front + server) |

## Brewfile

Single source of truth for CLI tooling. To add a tool that the team needs everywhere:

1. Add a `brew "..."` line to `Brewfile`
2. Run `make brewfile` to install locally
3. Commit and push — CI re-validates the file via `.github/workflows/bootstrap-ci.yml`

## CI

`.github/workflows/bootstrap-ci.yml` runs on any change to:
- `scripts/install-homebrew.sh`
- `setup-production.sh`
- `Brewfile`
- `Makefile`

It:
1. Lints both bash scripts with `shellcheck -S warning`
2. Runs `install-homebrew.sh` end-to-end on a fresh Ubuntu runner (with cache on `~/.linuxbrew`)
3. Validates the Brewfile is parseable

The cache key is `brew-${OS}-${hash(Brewfile)}` so subsequent runs reuse the Cellar between Brewfile changes.

## Production setup (StudentFlow)

`setup-production.sh` is the one-shot script for the StudentFlow API. It now auto-bootstraps required CLIs:

- **Step 0 (auto)**: Homebrew → Brewfile → supabase CLI (defensive fallback) → railway CLI (npm)
- **Step 1**: Apply Supabase schema
- **Step 2**: Configure Railway env vars (SMTP/Brevo, PUBLIC_BASE_URL, Supabase keys)
- **Step 3**: Smoke-test the live API

To skip Step 0 (e.g. on a runner where CLIs are already cached):

```bash
SKIP_BOOTSTRAP=1 ./setup-production.sh
```

## Troubleshooting

**`brew: command not found` after running `make brew`**
The PATH update is written to `~/.bashrc` / `~/.zshrc` but not eval'd in your current shell. Run:
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"   # Linux
eval "$(/opt/homebrew/bin/brew shellenv)"                # macOS Apple Silicon
```
Or open a new shell.

**`Don't run this as root!` from brew**
Use the wrapper at `/usr/local/bin/brew` (created automatically by `scripts/install-homebrew.sh` when run as root). It switches to the `linuxbrew` user transparently.

**Brewfile install fails on a single package**
`brew bundle install --no-lock` continues on partial failures. Inspect with `make check` to see which packages are missing.
