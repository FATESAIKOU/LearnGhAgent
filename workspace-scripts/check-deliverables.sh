#!/usr/bin/env bash
# check-deliverables.sh — Verify that required deliverable files exist.
#
# Reads DELIVERABLES env var — comma-separated glob patterns relative to
# /workspace.  Supports {ISSUE_NUMBER} placeholder (expanded from the
# ISSUE_NUMBER env var set by the pipeline).
#
# Writes PHASE_STATUS=OK or PHASE_STATUS=FAIL to /workspace/.branch-vars.
# If DELIVERABLES is empty/unset, defaults to OK (no validation).
set -uo pipefail

BRANCH_VARS="/workspace/.branch-vars"

log() { echo "[check-deliverables] $*"; }

# Expand placeholders
DELIVERABLES="${DELIVERABLES:-}"
DELIVERABLES="${DELIVERABLES//\{ISSUE_NUMBER\}/${ISSUE_NUMBER:-0}}"
DELIVERABLES="${DELIVERABLES//\{BRANCH_NAME\}/${BRANCH_NAME:-unknown}}"

if [ -z "$DELIVERABLES" ]; then
    log "No DELIVERABLES specified, defaulting to OK"
    echo "PHASE_STATUS=OK" >> "$BRANCH_VARS"
    exit 0
fi

STATUS="OK"
IFS=',' read -ra PATTERNS <<< "$DELIVERABLES"

for pattern in "${PATTERNS[@]}"; do
    pattern=$(echo "$pattern" | xargs)  # trim whitespace
    [ -z "$pattern" ] && continue

    shopt -s nullglob
    matches=(/workspace/$pattern)
    shopt -u nullglob

    if [ ${#matches[@]} -eq 0 ]; then
        log "MISSING: $pattern"
        STATUS="FAIL"
    else
        for m in "${matches[@]}"; do
            log "Found: $m"
        done
    fi
done

echo "PHASE_STATUS=$STATUS" >> "$BRANCH_VARS"
log "PHASE_STATUS=$STATUS"
