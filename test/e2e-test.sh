#!/usr/bin/env bash
#
# e2e-test.sh — End-to-end test for the GitHub Issue Agent system.
#
# Usage:
#   bash test/e2e-test.sh <TARGET_ISSUE_REPO> <ISSUE_NUMBER> [WORKFLOW_NAME]
#
# Example:
#   bash test/e2e-test.sh FATESAIKOU/SelfImprovement 20 technical-investigation
#
# What it does:
#   1. Build Docker image
#   2. Set up labels on the issue to trigger the first phase
#   3. Start container (POLL_INTERVAL=10 so it loops through all phases)
#   4. Stream logs and wait for full workflow completion or timeout
#   5. Verify results: all phases ran, PR created, comments posted
#   6. Clean up container
#
# Prerequisites:
#   - gh CLI authenticated on host
#   - auth/hosts.yml exists
#   - Docker running
#

set -euo pipefail

# ──────────────────────────────────────────────
# Args
# ──────────────────────────────────────────────
if [ $# -lt 2 ]; then
    echo "Usage: $0 <TARGET_ISSUE_REPO> <ISSUE_NUMBER> [WORKFLOW_NAME]"
    echo "Example: $0 FATESAIKOU/SelfImprovement 20 technical-investigation"
    exit 1
fi

TARGET_ISSUE_REPO="$1"
ISSUE_NUMBER="$2"
WORKFLOW_NAME="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTAINER_NAME="learnghagent-e2e-test"
TEST_TIMEOUT="${TEST_TIMEOUT:-3600}"   # 60 min default (multi-phase)
AGENT_TIMEOUT="${AGENT_TIMEOUT:-600}"  # 10 min per phase
POLL_INTERVAL="${POLL_INTERVAL:-10}"   # seconds between polls
COPILOT_MODEL="${COPILOT_MODEL:-}"

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
log()   { echo "[$(date +%H:%M:%S)] $*"; }
pass()  { echo "  ✅ $*"; }
fail()  { echo "  ❌ $*"; }
abort() { echo "FATAL: $*" >&2; cleanup; exit 1; }

cleanup() {
    log "Cleaning up..."
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

# ──────────────────────────────────────────────
# 0. Pre-checks
# ──────────────────────────────────────────────
log "=== Pre-checks ==="

[ -f "$PROJECT_ROOT/auth/hosts.yml" ] || abort "auth/hosts.yml not found"
pass "auth/hosts.yml exists"

docker info >/dev/null 2>&1 || abort "Docker is not running"
pass "Docker is running"

gh auth status >/dev/null 2>&1 || abort "gh CLI not authenticated"
pass "gh CLI authenticated"

# ──────────────────────────────────────────────
# 1. Build image
# ──────────────────────────────────────────────
log "=== Building Docker image ==="
docker build -t learnghagent:latest "$PROJECT_ROOT" -q
pass "Image built"

# ──────────────────────────────────────────────
# 2. Resolve workflow and set up labels
# ──────────────────────────────────────────────
log "=== Setting up issue labels ==="

# Read first phase from workflow YAML
if [ -n "$WORKFLOW_NAME" ]; then
    FIRST_ROLE=$(python3 -c "
import yaml, sys
with open('$PROJECT_ROOT/workflows/default.yml') as f:
    data = yaml.safe_load(f)
wf = data.get('$WORKFLOW_NAME')
if not wf:
    print('ERROR: workflow not found', file=sys.stderr); sys.exit(1)
steps = wf.get('steps', [])
if not steps:
    print('ERROR: no steps', file=sys.stderr); sys.exit(1)
print(steps[0]['role'])
")
    FIRST_PHASE=$(python3 -c "
import yaml
with open('$PROJECT_ROOT/workflows/default.yml') as f:
    data = yaml.safe_load(f)
print(data['$WORKFLOW_NAME']['steps'][0]['phasename'])
")
    TOTAL_PHASES=$(python3 -c "
import yaml
with open('$PROJECT_ROOT/workflows/default.yml') as f:
    data = yaml.safe_load(f)
print(len(data['$WORKFLOW_NAME']['steps']))
")
    log "Workflow: $WORKFLOW_NAME, first phase: $FIRST_ROLE / $FIRST_PHASE ($TOTAL_PHASES phases total)"

    # Clean existing role/phase/workflow labels (only remove from issue, not from repo)
    REMOVE_ARGS=""
    EXISTING_LABELS=$(GH_PAGER=cat gh issue view "$ISSUE_NUMBER" --repo "$TARGET_ISSUE_REPO" --json labels -q '.labels[].name' 2>/dev/null || true)
    while IFS= read -r label; do
        case "$label" in
            role:*|phase:*|workflow:*)
                REMOVE_ARGS="$REMOVE_ARGS --remove-label \"$label\""
                ;;
        esac
    done <<< "$EXISTING_LABELS"
    if [ -n "$REMOVE_ARGS" ]; then
        eval gh issue edit "$ISSUE_NUMBER" --repo "$TARGET_ISSUE_REPO" $REMOVE_ARGS 2>/dev/null || true
    fi

    # Ensure labels exist in repo, then add to issue
    for lbl in "workflow:$WORKFLOW_NAME"; do
        gh label create "$lbl" --repo "$TARGET_ISSUE_REPO" 2>/dev/null || true
    done
    gh issue edit "$ISSUE_NUMBER" --repo "$TARGET_ISSUE_REPO" \
        --add-label "workflow:$WORKFLOW_NAME" || abort "Failed to set labels"
    pass "Labels set: workflow:$WORKFLOW_NAME"
else
    log "No workflow specified — assuming labels are already set on issue #$ISSUE_NUMBER"
fi

# ──────────────────────────────────────────────
# 3. Start container
# ──────────────────────────────────────────────
log "=== Starting agent container ==="

# Remove stale container
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

docker run -d \
    --name "$CONTAINER_NAME" \
    -e "TARGET_ISSUE_REPO=$TARGET_ISSUE_REPO" \
    -e "POLL_INTERVAL=$POLL_INTERVAL" \
    -e "AGENT_TIMEOUT=$AGENT_TIMEOUT" \
    -e "COPILOT_MODEL=$COPILOT_MODEL" \
    -v "$PROJECT_ROOT/auth/hosts.yml:/auth-src/hosts.yml:ro" \
    -v "$PROJECT_ROOT/agents:/app/agents:ro" \
    -v "$PROJECT_ROOT/workflows:/app/workflows:ro" \
    -v "$PROJECT_ROOT/workspace-scripts:/app/workspace-scripts:ro" \
    -v "$PROJECT_ROOT/workspace:/workspace" \
    learnghagent:latest

pass "Container started: $CONTAINER_NAME"

# ──────────────────────────────────────────────
# 4. Stream logs and wait for completion
# ──────────────────────────────────────────────
log "=== Monitoring agent (timeout: ${TEST_TIMEOUT}s) ==="
log "Logs:"

START_TIME=$(date +%s)
RESULT="unknown"

# Follow logs in background, capture to file
LOG_FILE=$(mktemp)
docker logs -f "$CONTAINER_NAME" > "$LOG_FILE" 2>&1 &
LOG_PID=$!

# Also tail to stdout
tail -f "$LOG_FILE" &
TAIL_PID=$!

# Wait for completion signals in logs
while true; do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ "$ELAPSED" -ge "$TEST_TIMEOUT" ]; then
        RESULT="timeout"
        break
    fi

    # Check if container is still running
    if ! docker inspect "$CONTAINER_NAME" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
        # Container exited — check if it was the sleep (normal completion)
        RESULT="container-exited"
        break
    fi

    # Check for full workflow completion
    if grep -q "completed (branch target=end), set phase:end" "$LOG_FILE" 2>/dev/null; then
        RESULT="completed"
        break
    fi

    # Check for fatal errors
    if grep -q "ERROR.*workspace-init failed" "$LOG_FILE" 2>/dev/null; then
        RESULT="init-failed"
        break
    fi

    sleep 5
done

# Stop tailing
kill "$TAIL_PID" 2>/dev/null || true
kill "$LOG_PID" 2>/dev/null || true

echo ""
log "Agent finished with result: $RESULT (elapsed: ${ELAPSED}s)"

# ──────────────────────────────────────────────
# 5. Verify results
# ──────────────────────────────────────────────
log "=== Verification ==="

ERRORS=0

# 5a. Check all phases ran
PHASES_PROCESSED=$(grep -c "processing (role=" "$LOG_FILE" 2>/dev/null || true)
PHASES_PROCESSED=${PHASES_PROCESSED:-0}
if [ -n "${TOTAL_PHASES:-}" ] && [ "$PHASES_PROCESSED" -ge "$TOTAL_PHASES" ]; then
    pass "All $TOTAL_PHASES phases processed ($PHASES_PROCESSED executions)"
elif [ "$PHASES_PROCESSED" -gt 0 ]; then
    fail "Only $PHASES_PROCESSED/${TOTAL_PHASES:-?} phases processed"
    ERRORS=$((ERRORS + 1))
else
    fail "No phases processed"
    ERRORS=$((ERRORS + 1))
fi

# 5b. Check workflow completed
if grep -q "completed (branch target=end), set phase:end" "$LOG_FILE" 2>/dev/null; then
    pass "Workflow completed successfully"
else
    fail "Workflow did NOT complete"
    ERRORS=$((ERRORS + 1))
fi

# 5c. Check workspace-init/cleanup hooks ran
INIT_COUNT=$(grep -c "running workspace-init scripts" "$LOG_FILE" 2>/dev/null || true)
INIT_COUNT=${INIT_COUNT:-0}
CLEANUP_COUNT=$(grep -c "running workspace-cleanup scripts\|Running workspace script: unban-git-write.sh" "$LOG_FILE" 2>/dev/null || true)
CLEANUP_COUNT=${CLEANUP_COUNT:-0}
if [ "$INIT_COUNT" -gt 0 ] && [ "$CLEANUP_COUNT" -gt 0 ]; then
    pass "Workspace hooks executed (init: $INIT_COUNT, cleanup: $CLEANUP_COUNT)"
else
    fail "Workspace hooks missing (init: $INIT_COUNT, cleanup: $CLEANUP_COUNT)"
    ERRORS=$((ERRORS + 1))
fi

# 5d. Check push happened
if grep -q "pushed changes for issue" "$LOG_FILE" 2>/dev/null; then
    PUSH_COUNT=$(grep -c "pushed changes for issue" "$LOG_FILE" 2>/dev/null || true)
    PUSH_COUNT=${PUSH_COUNT:-0}
    pass "Changes pushed ($PUSH_COUNT time(s))"
elif grep -q "no changes to push" "$LOG_FILE" 2>/dev/null; then
    log "  ⚠️  No changes pushed (agent may not have written files)"
else
    fail "No push activity found in logs"
    ERRORS=$((ERRORS + 1))
fi

# 5e. Check comments posted
COMMENT_COUNT=$(grep -c "comment posted" "$LOG_FILE" 2>/dev/null || true)
COMMENT_COUNT=${COMMENT_COUNT:-0}
if [ "$COMMENT_COUNT" -gt 0 ]; then
    pass "Agent posted $COMMENT_COUNT comment(s)"
else
    fail "No agent comments found in logs"
    ERRORS=$((ERRORS + 1))
fi

# 5f. Check PR exists (if workflow has repos)
if [ -n "$WORKFLOW_NAME" ]; then
    BRANCH="agent/issue-$ISSUE_NUMBER"
    TARGET_CODE_REPO=$(python3 -c "
import yaml
with open('$PROJECT_ROOT/workflows/default.yml') as f:
    data = yaml.safe_load(f)
wf = data.get('$WORKFLOW_NAME', {})
repos = wf.get('config', [])
if repos:
    print(repos[0]['repo'])
" 2>/dev/null || true)

    if [ -n "$TARGET_CODE_REPO" ]; then
        PR_URL=$(GH_PAGER=cat gh pr list --repo "$TARGET_CODE_REPO" --head "$BRANCH" --json number,url,state -q '.[0].url' 2>/dev/null || true)
        if [ -n "$PR_URL" ]; then
            pass "PR exists: $PR_URL"
        else
            fail "No PR found on $TARGET_CODE_REPO for branch $BRANCH"
            ERRORS=$((ERRORS + 1))
        fi
    fi
fi

# 5g. Check no "git blocked" errors
BLOCK_COUNT=$(grep -c "is blocked during agent execution" "$LOG_FILE" 2>/dev/null || true)
BLOCK_COUNT=${BLOCK_COUNT:-0}
if [ "$BLOCK_COUNT" -gt 0 ]; then
    log "  ⚠️  Agent hit git-write block $BLOCK_COUNT time(s) — wrapper is working but agent tried"
fi

# ──────────────────────────────────────────────
# 6. Summary
# ──────────────────────────────────────────────
echo ""
log "=== Summary ==="
log "Result: $RESULT"
log "Errors: $ERRORS"
log "Log file: $LOG_FILE"

if [ "$ERRORS" -eq 0 ] && [ "$RESULT" = "completed" ]; then
    log "🎉 E2E test PASSED"
    exit 0
else
    log "💥 E2E test FAILED"
    exit 1
fi
