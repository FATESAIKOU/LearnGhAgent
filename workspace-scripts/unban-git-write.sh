#!/bin/bash
# unban-git-write.sh — Remove the git wrapper installed by ban-git-write.sh.
#
# This restores normal git behaviour so the next agent step (or push_workspace)
# is not affected.

set -euo pipefail

WRAPPER=/usr/local/bin/git

if [ -f "$WRAPPER" ]; then
    rm -f "$WRAPPER"
    echo "[workspace-scripts] unban-git-write: wrapper removed"
else
    echo "[workspace-scripts] unban-git-write: no wrapper found, nothing to do"
fi
