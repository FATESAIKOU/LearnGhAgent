#!/bin/bash
# clone-and-branch.sh — Clone repos and checkout/create feature branch.
#
# Expected environment variables (set via workflow phase-env):
#   REPOS         — JSON array, e.g. [{"repo":"owner/name","url":"","description":"..."}]
#   ISSUE_NUMBER  — Issue number (e.g. 20)
#   BRANCH_NAME   — Branch name (e.g. agent/issue-20)
#
# Idempotent: safe to call repeatedly (fetches + checks out existing branch).
# Exit code non-zero → pipeline will skip this issue.

set -euo pipefail

WORKSPACE_ROOT="/workspace"
mkdir -p "$WORKSPACE_ROOT"

if [ -z "${REPOS:-}" ]; then
    echo "[clone-and-branch] ERROR: REPOS env var is not set" >&2
    exit 1
fi
if [ -z "${ISSUE_NUMBER:-}" ]; then
    echo "[clone-and-branch] ERROR: ISSUE_NUMBER env var is not set" >&2
    exit 1
fi

BRANCH="${BRANCH_NAME:-agent/issue-${ISSUE_NUMBER}}"

# Clear pre-agent HEAD file (used by check-deliverables.sh)
PRE_HEAD_FILE="${WORKSPACE_ROOT}/.pre-agent-head"
rm -f "$PRE_HEAD_FILE"

# Iterate over each repo in the JSON array
repo_count=$(echo "$REPOS" | jq '. | length')
for (( i=0; i<repo_count; i++ )); do
    repo=$(echo "$REPOS" | jq -r ".[$i].repo")
    url=$(echo "$REPOS" | jq -r ".[$i].url // \"\"")
    name="${repo##*/}"
    repo_dir="${WORKSPACE_ROOT}/${name}"

    echo "[clone-and-branch] Processing repo: ${repo} → ${repo_dir}"

    # --- Clone or fetch ---
    if [ ! -d "${repo_dir}/.git" ]; then
        echo "[clone-and-branch] Cloning ${repo}"
        if [ -n "$url" ]; then
            git clone "$url" "$repo_dir"
        else
            gh repo clone "$repo" "$repo_dir"
        fi
    else
        echo "[clone-and-branch] Fetching latest for ${name}"
        git -C "$repo_dir" fetch --all || echo "[clone-and-branch] WARNING: fetch failed for ${name}"
    fi

    # --- Detect default branch ---
    default_br=$(git -C "$repo_dir" symbolic-ref refs/remotes/origin/HEAD --short 2>/dev/null | sed 's|^origin/||' || true)
    if [ -z "$default_br" ]; then
        for candidate in main master; do
            if git -C "$repo_dir" rev-parse --verify "origin/${candidate}" >/dev/null 2>&1; then
                default_br="$candidate"
                break
            fi
        done
    fi
    default_br="${default_br:-main}"

    # --- Checkout / create branch ---
    if git -C "$repo_dir" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
        # Branch exists locally
        git -C "$repo_dir" checkout "$BRANCH"
        # Sync with remote to avoid non-fast-forward on push
        git -C "$repo_dir" reset --hard "origin/${BRANCH}" 2>/dev/null || true
        echo "[clone-and-branch] ${name}: checked out existing branch '${BRANCH}'"
    elif git -C "$repo_dir" rev-parse --verify "origin/${BRANCH}" >/dev/null 2>&1; then
        # Branch exists on remote only
        git -C "$repo_dir" checkout -b "$BRANCH" "origin/${BRANCH}"
        echo "[clone-and-branch] ${name}: checked out remote branch '${BRANCH}'"
    else
        # Create new branch from default
        git -C "$repo_dir" checkout "$default_br"
        git -C "$repo_dir" pull origin "$default_br" 2>/dev/null || true
        git -C "$repo_dir" checkout -b "$BRANCH"
        echo "[clone-and-branch] ${name}: created branch '${BRANCH}' from '${default_br}'"
    fi
    # Save HEAD hash for deliverable validation
    echo "${name}=$(git -C "$repo_dir" rev-parse HEAD)" >> "$PRE_HEAD_FILE"
done

echo "[clone-and-branch] Done — ${repo_count} repo(s) ready"
