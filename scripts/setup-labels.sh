#!/usr/bin/env bash
#
# setup-labels.sh — Create all GitHub labels needed by the workflow system.
#
# Reads a workflow YAML file and creates labels on the target repo:
#   - workflow:<name>     for each workflow
#   - role:<role>         for each unique role across all steps
#   - phase:<phasename>   for each unique phase across all steps
#   - phase:end           (always created — marks completed workflows)
#
# Usage:
#   bash scripts/setup-labels.sh <TARGET_REPO> [WORKFLOW_FILE]
#
# Example:
#   bash scripts/setup-labels.sh FATESAIKOU/SelfImprovement
#   bash scripts/setup-labels.sh FATESAIKOU/SelfImprovement workflows/default.yml
#
# Prerequisites:
#   - gh CLI authenticated
#   - python3 + PyYAML installed
#

set -euo pipefail

# ── Args ──
if [ $# -lt 1 ]; then
    echo "Usage: $0 <TARGET_REPO> [WORKFLOW_FILE]"
    echo "Example: $0 FATESAIKOU/SelfImprovement"
    exit 1
fi

TARGET_REPO="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_FILE="${2:-$PROJECT_ROOT/workflows/default.yml}"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "ERROR: Workflow file not found: $WORKFLOW_FILE" >&2
    exit 1
fi

# ── Extract labels from workflow YAML ──
LABELS=$(python3 -c "
import yaml, sys

with open('$WORKFLOW_FILE') as f:
    data = yaml.safe_load(f)

labels = set()
labels.add('phase:end')

for wf_name, wf_data in data.items():
    labels.add(f'workflow:{wf_name}')

    if isinstance(wf_data, list):
        steps = wf_data
    elif isinstance(wf_data, dict):
        steps = wf_data.get('steps', []) or []
    else:
        continue

    for step in steps:
        if not isinstance(step, dict):
            continue
        role = step.get('role', '')
        phasename = step.get('phasename', '')
        if role:
            labels.add(f'role:{role}')
        if phasename:
            labels.add(f'phase:{phasename}')

for lbl in sorted(labels):
    print(lbl)
")

if [ -z "$LABELS" ]; then
    echo "No labels found in $WORKFLOW_FILE"
    exit 1
fi

# ── Create labels on repo ──
TOTAL=$(echo "$LABELS" | wc -l | tr -d ' ')
CREATED=0
EXISTED=0

echo "Creating $TOTAL labels on $TARGET_REPO from $WORKFLOW_FILE"
echo ""

while IFS= read -r label; do
    if GH_PAGER=cat gh label create "$label" --repo "$TARGET_REPO" 2>/dev/null; then
        echo "  ✅ Created: $label"
        CREATED=$((CREATED + 1))
    else
        echo "  ⏭  Already exists: $label"
        EXISTED=$((EXISTED + 1))
    fi
done <<< "$LABELS"

echo ""
echo "Done: $CREATED created, $EXISTED already existed (total: $TOTAL)"
