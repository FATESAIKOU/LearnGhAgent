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

# ── Install gh copilot extension ──
echo "[ENTRYPOINT] Installing gh copilot extension..."
gh extension install github/gh-copilot --force 2>&1 || {
    echo "  ⚠️  gh copilot extension install failed (may already exist)"
}

# ── Verify ──
echo "[ENTRYPOINT] Verifying setup..."
gh auth status 2>&1 || true
echo ""

# ── Run workflow ──
echo "[ENTRYPOINT] Starting PoC workflow..."
exec python3 /app/src/main_poc.py "$@"
