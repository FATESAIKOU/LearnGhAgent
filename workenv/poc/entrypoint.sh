#!/bin/bash
set -euo pipefail

# ── Setup gh auth ──
echo "[ENTRYPOINT] Setting up gh auth..."
mkdir -p ~/.config/gh

if [ -f /auth-src/hosts.yml ]; then
    cp /auth-src/hosts.yml ~/.config/gh/hosts.yml
    chmod 600 ~/.config/gh/hosts.yml
    echo "  ✅ Auth config copied"
else
    echo "  ❌ /auth-src/hosts.yml not found!"
    exit 1
fi

# ── Setup git credential helper (for push) ──
echo "[ENTRYPOINT] Setting up git credential helper..."
gh auth setup-git 2>&1 || true

# ── Install Copilot CLI ──
echo "[ENTRYPOINT] Installing Copilot CLI..."
npm install -g @github/copilot 2>&1 | tail -3
echo "  Copilot CLI version: $(copilot --version 2>&1)"

# ── Verify ──
echo "[ENTRYPOINT] Verifying setup..."
gh auth status 2>&1 || true
echo "  COPILOT_MODEL=${COPILOT_MODEL:-gpt-5-mini}"
echo ""

# ── Run workflow ──
echo "[ENTRYPOINT] Starting PoC workflow..."
exec python3 /app/src/main_poc.py "$@"
