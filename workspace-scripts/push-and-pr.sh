#!/bin/bash
# push-and-pr.sh — Stage, commit, push changes and create draft PR.
#
# Expected environment variables (set via workflow phase-env):
#   REPOS         — JSON array, e.g. [{"repo":"owner/name","url":"","description":"..."}]
#   ISSUE_NUMBER  — Issue number (e.g. 20)
#   BRANCH_NAME   — Branch name (e.g. agent/issue-20)
#   ISSUE_REPO    — Issue tracking repo (e.g. FATESAIKOU/SelfImprovement)
#   PHASE_NAME    — Current phase name (e.g. implementation)
#
# IMPORTANT: All git calls use /usr/bin/git (absolute path) to bypass
# the ban-git-write.sh wrapper that may still be on PATH.
#
# Exit code is always 0 — push failure should not block comment/transition.
# Errors are logged but the script continues.

set -uo pipefail
# NOTE: no -e — we handle errors per-repo to continue on failure

GIT=/usr/bin/git
WORKSPACE_ROOT="/workspace"

if [ -z "${REPOS:-}" ]; then
    echo "[push-and-pr] ERROR: REPOS env var is not set" >&2
    exit 0  # non-blocking
fi
if [ -z "${ISSUE_NUMBER:-}" ]; then
    echo "[push-and-pr] ERROR: ISSUE_NUMBER env var is not set" >&2
    exit 0
fi

BRANCH="${BRANCH_NAME:-agent/issue-${ISSUE_NUMBER}}"
PHASE="${PHASE_NAME:-}"
TRACKING_REPO="${ISSUE_REPO:-}"

# Expand COMMIT_SCOPE placeholders (limits git-add to a subdirectory)
COMMIT_SCOPE="${COMMIT_SCOPE:-}"
COMMIT_SCOPE="${COMMIT_SCOPE//\{ISSUE_NUMBER\}/${ISSUE_NUMBER}}"
COMMIT_SCOPE="${COMMIT_SCOPE//\{BRANCH_NAME\}/${BRANCH}}"

repo_count=$(echo "$REPOS" | jq '. | length')
for (( i=0; i<repo_count; i++ )); do
    repo=$(echo "$REPOS" | jq -r ".[$i].repo")
    name="${repo##*/}"
    repo_dir="${WORKSPACE_ROOT}/${name}"

    if [ ! -d "${repo_dir}/.git" ]; then
        echo "[push-and-pr] WARNING: ${repo_dir} not found, skip"
        continue
    fi

    echo "[push-and-pr] Processing repo: ${repo}"

    # --- Stage changes (scoped or full) ---
    if [ -n "$COMMIT_SCOPE" ]; then
        $GIT -C "$repo_dir" add -- "$COMMIT_SCOPE" 2>/dev/null || true
    else
        status=$($GIT -C "$repo_dir" status --porcelain 2>/dev/null || true)
        if [ -n "$status" ]; then
            $GIT -C "$repo_dir" add -A
        fi
    fi

    # --- Commit if there are staged changes ---
    staged=$($GIT -C "$repo_dir" diff --cached --name-only 2>/dev/null || true)
    if [ -n "$staged" ]; then
        msg="[Agent] Issue #${ISSUE_NUMBER}"
        if [ -n "$PHASE" ]; then
            msg="${msg} - ${PHASE}"
        fi
        $GIT -C "$repo_dir" commit -m "$msg" || {
            echo "[push-and-pr] WARNING: commit failed for ${name}"
            continue
        }
    fi

    # --- Check if there are commits to push ---
    need_push=true
    if $GIT -C "$repo_dir" rev-parse --verify "origin/${BRANCH}" >/dev/null 2>&1; then
        ahead=$($GIT -C "$repo_dir" rev-list "origin/${BRANCH}..${BRANCH}" --count 2>/dev/null || echo "0")
        if [ "$ahead" = "0" ]; then
            echo "[push-and-pr] ${name}: no changes to push"
            need_push=false
        fi
    fi

    # --- Push if needed ---
    if [ "$need_push" = true ]; then
        if ! $GIT -C "$repo_dir" push -u origin "$BRANCH" 2>&1; then
            echo "[push-and-pr] WARNING: push failed for ${name}"
            continue
        fi
        echo "[push-and-pr] ${name}: pushed changes for issue #${ISSUE_NUMBER}"
    fi

    # --- Create draft PR if none exists (always check, even without new push) ---
    existing_prs=$(gh pr list --repo "$repo" --head "$BRANCH" --json number --limit 1 2>/dev/null || echo "[]")
    if [ "$(echo "$existing_prs" | jq '. | length')" -gt 0 ]; then
        echo "[push-and-pr] ${name}: PR already exists"
        continue
    fi

    # Detect default branch
    default_br=$($GIT -C "$repo_dir" symbolic-ref refs/remotes/origin/HEAD --short 2>/dev/null | sed 's|^origin/||' || true)
    if [ -z "$default_br" ]; then
        for candidate in main master; do
            if $GIT -C "$repo_dir" rev-parse --verify "origin/${candidate}" >/dev/null 2>&1; then
                default_br="$candidate"
                break
            fi
        done
    fi
    default_br="${default_br:-main}"

    pr_title="[Agent] Issue #${ISSUE_NUMBER}"
    pr_body="Automated PR created by GitHub Issue Agent."
    if [ -n "$TRACKING_REPO" ]; then
        pr_body="${pr_body}\n\nTracking issue: ${TRACKING_REPO}#${ISSUE_NUMBER}"
    fi

    if gh pr create --repo "$repo" \
        --title "$pr_title" \
        --body "$(echo -e "$pr_body")" \
        --base "$default_br" \
        --head "$BRANCH" \
        --draft 2>&1; then
        echo "[push-and-pr] ${name}: created draft PR"
    else
        echo "[push-and-pr] WARNING: failed to create PR for ${name}"
    fi
done

echo "[push-and-pr] Done"
exit 0
