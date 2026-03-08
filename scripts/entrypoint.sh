#!/usr/bin/env bash
set -euo pipefail

log() {
    local level="$1"
    shift
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [${level}] $*"
}

# --- Auth 設定（從 ro mount copy 到可寫位置）---
log INFO "Setting up auth..."
if [ ! -f /auth-src/hosts.yml ]; then
    log ERROR "Auth file not found. Mount hosts.yml to /auth-src/hosts.yml"
    exit 1
fi

mkdir -p /root/.config/gh
cp /auth-src/hosts.yml /root/.config/gh/hosts.yml
chmod 600 /root/.config/gh/hosts.yml

# --- 驗證 ---
if [ -z "${TARGET_ISSUE_REPO:-}" ]; then
    log ERROR "TARGET_ISSUE_REPO is required"
    exit 1
fi

log INFO "Verifying gh auth..."
if ! gh auth status 2>&1; then
    log ERROR "gh auth failed. Check auth/hosts.yml content."
    exit 1
fi

log INFO "Verifying gh copilot..."
if ! gh copilot -- --version 2>&1; then
    log ERROR "gh copilot CLI not found. Dockerfile build may have failed."
    exit 1
fi

# --- Git config for agent commits ---
git config --global user.name "GitHub Issue Agent"
git config --global user.email "agent@learnghagent.local"
git config --global --add safe.directory '*'
git config --global credential.helper '!gh auth git-credential'
log INFO "Git identity configured"

# --- 啟動主迴圈 ---
log INFO "Starting agent loop for ${TARGET_ISSUE_REPO}"
log INFO "Poll interval: ${POLL_INTERVAL:-60}s, Timeout: ${AGENT_TIMEOUT:-900}s"

exec python3 /app/agent_loop.py
