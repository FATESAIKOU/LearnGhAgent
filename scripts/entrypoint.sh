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
if [ -z "${TARGET_REPO:-}" ]; then
    log ERROR "TARGET_REPO is required"
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

# --- 初始化 ---
STATE_FILE="/data/state.json"
if [ ! -f "${STATE_FILE}" ]; then
    mkdir -p /data
    echo '{"issues":{}}' > "${STATE_FILE}"
    log INFO "Initialized state.json"
fi

# --- 啟動主迴圈 ---
log INFO "Starting agent loop for ${TARGET_REPO}"
log INFO "Poll interval: ${POLL_INTERVAL:-60}s, Timeout: ${AGENT_TIMEOUT:-900}s"

exec python3 /app/agent_loop.py
