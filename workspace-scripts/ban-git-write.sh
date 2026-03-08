#!/bin/bash
# ban-git-write.sh — Install a git wrapper that blocks write operations.
#
# The wrapper is placed at /usr/local/bin/git which takes priority
# over /usr/bin/git in PATH.  Read-only commands (status, diff, log, …)
# are passed through to the real git; write commands (checkout, commit,
# push, …) are rejected with an error message.
#
# To bypass the wrapper (e.g. in push_workspace), call /usr/bin/git directly.

set -euo pipefail

WRAPPER=/usr/local/bin/git
REAL_GIT=/usr/bin/git

cat > "$WRAPPER" << 'WRAPPER_SCRIPT'
#!/bin/bash
# Git wrapper — blocks write operations during agent execution.
REAL_GIT=/usr/bin/git

# Extract the git subcommand (skip global flags like -C, -c, --git-dir …)
subcmd=""
for arg in "$@"; do
    case "$arg" in
        -*) continue ;;
        *)  subcmd="$arg"; break ;;
    esac
done

# Blocked write operations
case "$subcmd" in
    checkout|switch|commit|push|reset|rebase|merge|branch|stash|cherry-pick|revert|pull|am|apply)
        echo "ERROR: 'git $subcmd' is blocked during agent execution." >&2
        echo "The system manages git operations automatically." >&2
        exit 1
        ;;
esac

# Allow everything else (status, diff, log, show, ls-files, …)
exec "$REAL_GIT" "$@"
WRAPPER_SCRIPT

chmod +x "$WRAPPER"
echo "[workspace-scripts] ban-git-write: wrapper installed at $WRAPPER"
