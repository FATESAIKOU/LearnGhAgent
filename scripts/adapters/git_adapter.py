"""Git adapter — implements GitPort using git and gh CLI."""

import json
import logging
import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.workflow import RepoConfig

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = "/workspace"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _run_cmd(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> str:
    """Run a command and return stdout."""
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _get_default_branch(repo_dir: str) -> str:
    """Detect the default branch of a repo (main or master)."""
    try:
        ref = _run_cmd(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
            cwd=repo_dir,
        )
        return ref.split("/")[-1]
    except Exception:
        for name in ("main", "master"):
            try:
                _run_cmd(
                    ["git", "rev-parse", "--verify", f"origin/{name}"],
                    cwd=repo_dir,
                )
                return name
            except Exception:
                continue
        return "main"


def _repo_dir_name(repo: str) -> str:
    """Extract directory name from 'owner/repo' format."""
    return repo.split("/")[-1] if "/" in repo else repo


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class GitCliAdapter:
    """Implements GitPort via git CLI and gh CLI."""

    def init_workspace(self, repos: list["RepoConfig"], issue_number: int) -> None:
        """Clone repos and create/checkout feature branches.

        Idempotent: safe to call repeatedly (fetches + checks out existing branch).
        """
        os.makedirs(WORKSPACE_ROOT, exist_ok=True)
        branch = f"agent/issue-{issue_number}"

        for rc in repos:
            name = _repo_dir_name(rc.repo)
            repo_dir = os.path.join(WORKSPACE_ROOT, name)

            # --- Clone or fetch ---
            if not os.path.isdir(os.path.join(repo_dir, ".git")):
                logger.info("Cloning %s → %s", rc.repo, repo_dir)
                if rc.url:
                    _run_cmd(["git", "clone", rc.url, repo_dir], timeout=300)
                else:
                    _run_cmd(["gh", "repo", "clone", rc.repo, repo_dir], timeout=300)
            else:
                logger.info("Fetching latest for %s", name)
                try:
                    _run_cmd(["git", "fetch", "--all"], cwd=repo_dir)
                except Exception as e:
                    logger.warning("git fetch failed for %s: %s", name, e)

            # --- Checkout / create branch ---
            default_br = _get_default_branch(repo_dir)
            try:
                # Branch exists locally
                _run_cmd(["git", "rev-parse", "--verify", branch], cwd=repo_dir)
                _run_cmd(["git", "checkout", branch], cwd=repo_dir)
                # Sync with remote to avoid non-fast-forward on push
                try:
                    _run_cmd(
                        ["git", "reset", "--hard", f"origin/{branch}"],
                        cwd=repo_dir,
                    )
                except Exception:
                    pass  # remote branch may not exist yet (before first push)
                logger.info("%s: checked out existing branch '%s'", name, branch)
            except Exception:
                try:
                    # Branch exists on remote
                    _run_cmd(
                        ["git", "rev-parse", "--verify", f"origin/{branch}"],
                        cwd=repo_dir,
                    )
                    _run_cmd(
                        ["git", "checkout", "-b", branch, f"origin/{branch}"],
                        cwd=repo_dir,
                    )
                    logger.info("%s: checked out remote branch '%s'", name, branch)
                except Exception:
                    # Create new branch from default
                    _run_cmd(["git", "checkout", default_br], cwd=repo_dir)
                    try:
                        _run_cmd(["git", "pull", "origin", default_br], cwd=repo_dir)
                    except Exception:
                        pass
                    _run_cmd(["git", "checkout", "-b", branch], cwd=repo_dir)
                    logger.info(
                        "%s: created branch '%s' from '%s'", name, branch, default_br
                    )

    def push_workspace(
        self,
        repos: list["RepoConfig"],
        issue_number: int,
        issue_repo: str,
        phase_name: str = "",
    ) -> None:
        """Stage, commit, and push changes for all workspace repos.

        Creates a draft PR if one doesn't already exist.
        """
        branch = f"agent/issue-{issue_number}"

        for rc in repos:
            name = _repo_dir_name(rc.repo)
            repo_dir = os.path.join(WORKSPACE_ROOT, name)

            if not os.path.isdir(os.path.join(repo_dir, ".git")):
                logger.warning("Repo dir %s not found, skip push", repo_dir)
                continue

            try:
                # Stage any uncommitted changes first
                status = _run_cmd(["git", "status", "--porcelain"], cwd=repo_dir)
                if status:
                    _run_cmd(["git", "add", "-A"], cwd=repo_dir)
                    msg = f"[Agent] Issue #{issue_number}"
                    if phase_name:
                        msg += f" - {phase_name}"
                    _run_cmd(["git", "commit", "-m", msg], cwd=repo_dir)

                # Check if local branch is ahead of origin
                try:
                    _run_cmd(
                        ["git", "rev-parse", "--verify", f"origin/{branch}"],
                        cwd=repo_dir,
                    )
                    diff = _run_cmd(
                        ["git", "rev-list", f"origin/{branch}..{branch}", "--count"],
                        cwd=repo_dir,
                    )
                    if diff.strip() == "0":
                        logger.info("%s: no changes to push", name)
                        continue
                except Exception:
                    # Origin branch doesn't exist yet — definitely need to push
                    pass

                _run_cmd(["git", "push", "-u", "origin", branch], cwd=repo_dir)
                logger.info("%s: pushed changes for issue #%d", name, issue_number)

                # Create PR if none exists yet
                self._ensure_pr(rc, repo_dir, branch, issue_number, issue_repo)
            except Exception as e:
                logger.error("%s: push failed: %s", name, e)

    def _ensure_pr(
        self,
        rc: "RepoConfig",
        repo_dir: str,
        branch: str,
        issue_number: int,
        issue_repo: str,
    ) -> None:
        """Create a draft PR if one doesn't already exist for this branch."""
        try:
            raw = _run_cmd(
                ["gh", "pr", "list", "--head", branch, "--json", "number", "--limit", "1"],
                cwd=repo_dir,
            )
            prs = json.loads(raw) if raw else []
            if prs:
                logger.debug("PR already exists for %s branch '%s'", rc.repo, branch)
                return
        except Exception:
            pass  # Can't check — try creating anyway

        default_br = _get_default_branch(repo_dir)

        title = f"[Agent] Issue #{issue_number}"
        body = (
            f"Automated PR created by GitHub Issue Agent.\n\n"
            f"Tracking issue: {issue_repo}#{issue_number}"
        )
        try:
            _run_cmd(
                [
                    "gh", "pr", "create",
                    "--title", title,
                    "--body", body,
                    "--base", default_br,
                    "--head", branch,
                    "--draft",
                ],
                cwd=repo_dir,
            )
            logger.info("Created draft PR for %s branch '%s'", rc.repo, branch)
        except Exception as e:
            logger.warning("Failed to create PR for %s: %s", rc.repo, e)
