"""GitHub API wrapper using gh CLI."""

import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


def _run_gh(*args: str) -> str:
    """Run a gh CLI command and return stdout."""
    cmd = ["gh"] + list(args)
    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"gh command failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()


def list_open_issues(repo: str) -> list[dict[str, Any]]:
    """Return all open issues as list of {number, labels}."""
    raw = _run_gh(
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--json", "number,labels",
        "--limit", "100",
    )
    return json.loads(raw) if raw else []


def get_issue(owner: str, repo: str, number: int) -> dict[str, Any]:
    """Return full issue data."""
    raw = _run_gh(
        "api", f"repos/{owner}/{repo}/issues/{number}",
    )
    return json.loads(raw)


def get_issue_comments(owner: str, repo: str, number: int) -> list[dict[str, Any]]:
    """Return all comments for an issue."""
    raw = _run_gh(
        "api", f"repos/{owner}/{repo}/issues/{number}/comments",
    )
    return json.loads(raw) if raw else []


def post_comment(repo: str, number: int, body: str) -> None:
    """Post a comment on an issue."""
    _run_gh(
        "issue", "comment", str(number),
        "--repo", repo,
        "--body", body,
    )
    logger.info("Issue #%d: comment posted", number)


def get_latest_activity_time(owner: str, repo: str, number: int) -> str:
    """Return the latest activity time (issue created_at or latest comment created_at)."""
    issue = get_issue(owner, repo, number)
    issue_created = issue.get("created_at", "")

    comments = get_issue_comments(owner, repo, number)
    if comments:
        comment_times = [c["created_at"] for c in comments if "created_at" in c]
        if comment_times:
            latest_comment = sorted(comment_times)[-1]
            return max(issue_created, latest_comment)

    return issue_created


def add_label(repo: str, number: int, label: str) -> None:
    """Add a label to an issue. Creates the label if it doesn't exist."""
    _run_gh(
        "issue", "edit", str(number),
        "--repo", repo,
        "--add-label", label,
    )
    logger.info("Issue #%d: added label '%s'", number, label)


def remove_label(repo: str, number: int, label: str) -> None:
    """Remove a label from an issue."""
    _run_gh(
        "issue", "edit", str(number),
        "--repo", repo,
        "--remove-label", label,
    )
    logger.info("Issue #%d: removed label '%s'", number, label)
