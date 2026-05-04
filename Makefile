# Makefile — SNB Consulting / La Francaise Des Sauces
# Single entry point for bootstrap and common dev tasks.
# Use `make help` to see available targets.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

ROOT := $(shell pwd)
BREW_PREFIX_LINUX := /home/linuxbrew/.linuxbrew
BREW_PREFIX_MAC   := /opt/homebrew

.PHONY: help bootstrap brew brewfile setup-prod lint clean-brew check doctor dev install

## help: List available targets
help:
	@grep -E '^## [a-zA-Z_-]+:' Makefile | awk -F': ' '{ sub(/^## /,"",$$1); printf "  %-14s %s\n", $$1, $$2 }'

## bootstrap: Install Homebrew + apply Brewfile (one shot, idempotent)
bootstrap: brew brewfile
	@echo "✅ Bootstrap complete"

## brew: Install Homebrew if missing
brew:
	@if ! command -v brew >/dev/null 2>&1 \
		&& [ ! -x $(BREW_PREFIX_LINUX)/bin/brew ] \
		&& [ ! -x $(BREW_PREFIX_MAC)/bin/brew ]; then \
		NONINTERACTIVE=1 ./scripts/install-homebrew.sh ; \
	else \
		echo "✓ Homebrew already installed" ; \
	fi

## brewfile: Apply Brewfile (install missing packages)
brewfile:
	@if [ -x $(BREW_PREFIX_LINUX)/bin/brew ]; then \
		eval "$$($(BREW_PREFIX_LINUX)/bin/brew shellenv)" && brew bundle install --no-lock --file=Brewfile ; \
	elif [ -x $(BREW_PREFIX_MAC)/bin/brew ]; then \
		eval "$$($(BREW_PREFIX_MAC)/bin/brew shellenv)" && brew bundle install --no-lock --file=Brewfile ; \
	else \
		brew bundle install --no-lock --file=Brewfile ; \
	fi

## check: Verify Brewfile state without installing
check:
	@brew bundle check --verbose --file=Brewfile || true

## clean-brew: Uninstall packages not listed in Brewfile (DESTRUCTIVE — confirm)
clean-brew:
	@echo "⚠️  This will uninstall any brew package NOT listed in Brewfile."
	@read -p "Continue? [y/N] " ans && [ "$$ans" = "y" ] || exit 1
	@brew bundle cleanup --force --file=Brewfile

## setup-prod: Run full production setup (StudentFlow)
setup-prod:
	@./setup-production.sh

## lint: Shellcheck the bootstrap scripts
lint:
	@shellcheck -S warning scripts/install-homebrew.sh setup-production.sh

## doctor: Run brew doctor for diagnostics
doctor:
	@brew doctor || true

## install: Install npm deps for the LFDS quiz front+server
install:
	@npm install

## dev: Start dev servers (front + API)
dev:
	@npm run dev
