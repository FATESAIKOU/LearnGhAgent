#!/bin/bash
set -euo pipefail

# Usage: bash scripts/launch_workflow_learn-tech.sh <repo> <issue_id> <branch_name>
# Example: bash scripts/launch_workflow_learn-tech.sh FATESAIKOU/SelfImprovement 20 technical-investigation

REPO="${1:?Usage: $0 <repo> <issue_id> <branch_name>}"
ISSUE_ID="${2:?}"
BRANCH_NAME="${3:?}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Load .env ──
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

echo "============================================================"
echo " LearnTech Workflow Launcher"
echo "============================================================"
echo " Repo:   $REPO"
echo " Issue:  #$ISSUE_ID"
echo " Branch: $BRANCH_NAME"
echo " Model:  ${COPILOT_MODEL:-gpt-5-mini}"
echo "============================================================"
echo ""

# ── Build Docker image ──
echo "[LAUNCH] Building Docker image..."
docker build \
    -f "$PROJECT_DIR/workenv/learn-tech/Dockerfile" \
    -t learn-tech \
    "$PROJECT_DIR"
echo ""

# ── Run container ──
echo "[LAUNCH] Running LearnTech workflow in Docker..."
docker run --rm \
    -v "$PROJECT_DIR/auth/hosts.yml:/auth-src/hosts.yml:ro" \
    -e "COPILOT_MODEL=${COPILOT_MODEL:-gpt-5-mini}" \
    learn-tech \
    "$REPO" "$ISSUE_ID" "$BRANCH_NAME"
