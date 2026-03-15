"""
GitHelper: Git 操作 helper。

職責：
  - clone repo + checkout branch
  - remove origin（安全）
  - commit（allow empty）
  - add origin + push

不做：
  - 決定節點邏輯
  - 決定 status
  - GitHub API 操作
"""

import subprocess


class GitHelper:
    """Git CLI wrapper for repository operations."""

    @staticmethod
    def _run_git(args: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run git command."""
        print(f"  [GIT] {' '.join(args)}")
        return subprocess.run(args, capture_output=True, text=True, cwd=cwd)

    @staticmethod
    def clone_and_checkout(repo: str, branch_name: str) -> str:
        """Clone repo and checkout branch. Returns local path."""
        local_path = f"/tmp/learn-tech-{repo.replace('/', '-')}"

        # Clean previous
        subprocess.run(["rm", "-rf", local_path], capture_output=True)

        # Clone via gh
        r = GitHelper._run_git(["gh", "repo", "clone", repo, local_path])
        if r.returncode != 0:
            raise RuntimeError(f"Clone failed: {r.stderr.strip()}")
        print("  ✅ Clone OK")

        # Checkout branch
        r = GitHelper._run_git(["git", "checkout", branch_name], cwd=local_path)
        if r.returncode != 0:
            print(f"  ⚠️  Checkout: {r.stderr.strip()}")
        else:
            print("  ✅ Checkout OK")

        return local_path

    @staticmethod
    def remove_origin(local_path: str) -> None:
        """Remove git origin to prevent accidental writes during node execution."""
        GitHelper._run_git(["git", "remote", "remove", "origin"], cwd=local_path)
        print("  ✅ Origin removed")

    @staticmethod
    def commit(local_path: str, node_name: str, status: str) -> None:
        """Commit current state with node name as title (allow empty)."""
        msg = f"[learn-tech] {node_name}: {status}"
        GitHelper._run_git(["git", "add", "-A"], cwd=local_path)
        GitHelper._run_git(
            ["git", "commit", "--allow-empty", "-m", msg],
            cwd=local_path,
        )

    @staticmethod
    def add_origin_and_push(local_path: str, repo: str, branch_name: str) -> None:
        """Add origin back and push."""
        repo_url = f"https://github.com/{repo}.git"

        GitHelper._run_git(
            ["git", "remote", "add", "origin", repo_url],
            cwd=local_path,
        )

        r = GitHelper._run_git(
            ["git", "push", "origin", branch_name],
            cwd=local_path,
        )
        if r.returncode == 0:
            print("  ✅ Push OK")
        else:
            print(f"  ❌ Push FAILED: {r.stderr.strip()}")
