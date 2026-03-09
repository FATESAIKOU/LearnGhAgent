#!/usr/bin/env bash
# check-deliverables.sh — Verify that required deliverable files were
# produced (new or modified) in the current phase.
#
# Reads DELIVERABLES env var — comma-separated glob patterns relative to
# /workspace.  Supports {ISSUE_NUMBER} and {BRANCH_NAME} placeholders.
#
# Uses /workspace/.pre-agent-head (written by clone-and-branch.sh) to
# verify files appear in the git diff since the pre-agent HEAD, ensuring
# that pre-existing files from earlier runs do not falsely pass validation.
#
# Writes PHASE_STATUS=OK or PHASE_STATUS=FAIL to /workspace/.branch-vars.
# If DELIVERABLES is empty/unset, defaults to OK (no validation).
set -uo pipefail

BRANCH_VARS="/workspace/.branch-vars"
PRE_HEAD_FILE="/workspace/.pre-agent-head"
GIT=/usr/bin/git

log() { echo "[check-deliverables] $*"; }

# ---------- Load pre-agent HEAD hashes ----------
declare -A PRE_HEADS
if [ -f "$PRE_HEAD_FILE" ]; then
    while IFS='=' read -r rname rhash; do
        [ -z "$rname" ] && continue
        PRE_HEADS["$rname"]="$rhash"
    done < "$PRE_HEAD_FILE"
fi

# ---------- Expand placeholders ----------
DELIVERABLES="${DELIVERABLES:-}"
DELIVERABLES="${DELIVERABLES//\{ISSUE_NUMBER\}/${ISSUE_NUMBER:-0}}"
DELIVERABLES="${DELIVERABLES//\{BRANCH_NAME\}/${BRANCH_NAME:-unknown}}"

if [ -z "$DELIVERABLES" ]; then
    log "No DELIVERABLES specified, defaulting to OK"
    echo "PHASE_STATUS=OK" >> "$BRANCH_VARS"
    exit 0
fi

# ---------- Check each deliverable ----------
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
            # Determine repo name and relative path
            rel="${m#/workspace/}"
            repo_name="${rel%%/*}"
            file_rel="${rel#*/}"
            repo_dir="/workspace/${repo_name}"
            pre_head="${PRE_HEADS[$repo_name]:-}"

            if [ -n "$pre_head" ] && [ -d "${repo_dir}/.git" ]; then
                # Verify the file was added/modified since pre-agent HEAD
                diff_out=$($GIT -C "$repo_dir" diff --name-only "$pre_head" HEAD -- "$file_rel" 2>/dev/null || true)
                if [ -n "$diff_out" ]; then
                    log "Found (new/modified): $m"
                else
                    log "STALE (not modified in this phase): $m"
                    STATUS="FAIL"
                fi
            else
                # No baseline — fall back to existence check
                log "Found: $m"
            fi
        done
    fi
done

echo "PHASE_STATUS=$STATUS" >> "$BRANCH_VARS"
log "PHASE_STATUS=$STATUS"
