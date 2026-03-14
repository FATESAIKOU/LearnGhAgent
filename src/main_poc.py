"""
main_poc.py: PoC workflow orchestration。

職責：
  - setup（clone / checkout / remove origin / read issue / init state）
  - orchestration loop（get_next_node → run → comment → commit）
  - teardown（add origin / push）

不做：
  - prompt 組裝細節
  - LLM 呼叫細節
  - status 判定細節
  - comment 內容生成細節
"""

import sys
import os
import subprocess
import json

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lib.state import State
from src.nodes.poc.node_1_hello_llm import Node1HelloLlm
from src.nodes.poc.node_2_post_comment import Node2PostComment


# ──────────────────────────────────────────────
# Global Constants
# ──────────────────────────────────────────────

COPILOT_MODEL = os.environ.get("COPILOT_MODEL", "gpt-5-mini")


# ──────────────────────────────────────────────
# Transfer Matrix
# ──────────────────────────────────────────────

TRANSFER_MATRIX = {
    ("START", "SUCCESS"):                "node_1_hello_llm",
    ("node_1_hello_llm", "SUCCESS"):     "node_2_post_comment",
    ("node_1_hello_llm", "UNKNOWN"):     "node_1_hello_llm",
    ("node_1_hello_llm", "ERROR"):       "END",
    ("node_2_post_comment", "SUCCESS"):  "END",
    ("node_2_post_comment", "UNKNOWN"):  "node_2_post_comment",
    ("node_2_post_comment", "ERROR"):    "END",
}

MAX_RETRY = {
    ("node_1_hello_llm", "UNKNOWN"):     2,
    ("node_2_post_comment", "UNKNOWN"):  2,
}

NODE_MAP = {
    "node_1_hello_llm":    Node1HelloLlm,
    "node_2_post_comment": Node2PostComment,
}


# ──────────────────────────────────────────────
# Helper: run gh CLI
# ──────────────────────────────────────────────

def run_gh(args: list[str], check: bool = False) -> subprocess.CompletedProcess:
    """Run a gh CLI command and return the result."""
    print(f"  [GH] {' '.join(args)}")
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  [GH ERROR] {result.stderr.strip()}")
    return result


def run_git(args: list[str], cwd: str = None) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    print(f"  [GIT] {' '.join(args)}")
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


# ──────────────────────────────────────────────
# Orchestration
# ──────────────────────────────────────────────

def get_next_node(state: State) -> str:
    """Look up transfer matrix to determine next node. Returns 'END' if done or retry exceeded."""
    key = (state.from_node, state.status)
    next_name = TRANSFER_MATRIX.get(key, "END")

    if next_name == "END":
        return "END"

    # Check retry limit
    retry_count = state.retry_per_edge_cnt.get(key, 0)
    max_retry = MAX_RETRY.get(key, 0)

    if state.status in ("UNKNOWN", "NG") and retry_count >= max_retry:
        print(f"  [RETRY EXCEEDED] {key} retried {retry_count}/{max_retry} → END")
        return "END"

    # Increment retry counter
    state.retry_per_edge_cnt[key] = retry_count + 1
    return next_name


def setup(repo: str, issue_id: str, branch_name: str) -> State:
    """Clone repo, checkout branch, read issue, initialize state."""
    print("=" * 60)
    print(f"[SETUP] repo={repo} issue=#{issue_id} branch={branch_name}")
    print("=" * 60)

    # 1. Verify gh auth
    print("\n[1/5] Verifying gh auth...")
    r = run_gh(["gh", "auth", "status"])
    if r.returncode == 0:
        print("  ✅ Auth OK")
    else:
        print(f"  ❌ Auth FAILED: {r.stderr.strip()}")
        sys.exit(1)

    # 2. Clone repo
    local_path = f"/tmp/poc-{repo.replace('/', '-')}"
    print(f"\n[2/5] Cloning {repo} → {local_path}...")
    subprocess.run(["rm", "-rf", local_path])
    r = run_gh(["gh", "repo", "clone", repo, local_path])
    if r.returncode != 0:
        print(f"  ❌ Clone FAILED: {r.stderr.strip()}")
        sys.exit(1)
    print("  ✅ Clone OK")

    # 3. Checkout branch
    print(f"\n[3/5] Checking out branch: {branch_name}...")
    r = run_git(["git", "checkout", branch_name], cwd=local_path)
    if r.returncode != 0:
        print(f"  ⚠️  Checkout failed (may already be on branch): {r.stderr.strip()}")
    else:
        print("  ✅ Checkout OK")

    # 4. Remove origin (safety: prevent accidental push during node execution)
    print("\n[4/5] Removing origin (safety)...")
    run_git(["git", "remote", "remove", "origin"], cwd=local_path)
    print("  ✅ Origin removed")

    # 5. Read issue
    print(f"\n[5/5] Reading issue #{issue_id}...")
    r = run_gh([
        "gh", "issue", "view", str(issue_id),
        "--repo", repo,
        "--json", "title,body,comments",
    ])

    issue_title = ""
    issue_body = ""
    issue_comments = []

    if r.returncode == 0:
        try:
            data = json.loads(r.stdout)
            issue_title = data.get("title", "")
            issue_body = data.get("body", "")
            issue_comments = [c.get("body", "") for c in data.get("comments", [])]
            print(f"  ✅ Issue title: {issue_title}")
        except json.JSONDecodeError:
            print(f"  ⚠️  Failed to parse issue JSON: {r.stdout[:200]}")
    else:
        print(f"  ❌ Read issue FAILED: {r.stderr.strip()}")

    state = State(
        issue_id=int(issue_id),
        branch_name=branch_name,
        repo=repo,
        local_repo_path=local_path,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        from_node="START",
        status="SUCCESS",
    )

    print(f"\n{'=' * 60}")
    print("[SETUP DONE]")
    print(f"{'=' * 60}")
    return state


def comment_to_issue(state: State):
    """Post the latest node's output as a comment to the issue."""
    if not state.workflow_output_histories:
        return

    node_name, output = state.workflow_output_histories[-1]

    comment_body = (
        f"## 🤖 Workflow Node: `{node_name}`\n\n"
        f"**Status**: `{state.status}`\n\n"
        f"### Output\n\n"
        f"{output[:3000]}\n\n"
        f"---\n"
        f"_Posted by PoC workflow_"
    )

    print(f"  [COMMENT] Posting comment for {node_name}...")
    run_gh([
        "gh", "issue", "comment", str(state.issue_id),
        "--repo", state.repo,
        "--body", comment_body,
    ])


def git_commit(state: State):
    """Commit with node name as title (allow empty commits)."""
    if not state.workflow_output_histories:
        return

    node_name, _ = state.workflow_output_histories[-1]
    msg = f"[poc] {node_name}: {state.status}"

    run_git(["git", "add", "-A"], cwd=state.local_repo_path)
    run_git(
        ["git", "commit", "--allow-empty", "-m", msg],
        cwd=state.local_repo_path,
    )


def teardown(state: State):
    """Add origin back and push."""
    print(f"\n{'=' * 60}")
    print("[TEARDOWN]")
    print(f"{'=' * 60}")

    repo_url = f"https://github.com/{state.repo}.git"

    # Add origin back
    print(f"\n[1/2] Adding origin: {repo_url}")
    run_git(
        ["git", "remote", "add", "origin", repo_url],
        cwd=state.local_repo_path,
    )

    # Push
    print(f"[2/2] Pushing to {state.branch_name}...")
    r = run_git(
        ["git", "push", "origin", state.branch_name],
        cwd=state.local_repo_path,
    )
    if r.returncode == 0:
        print("  ✅ Push OK")
    else:
        print(f"  ❌ Push FAILED: {r.stderr.strip()}")

    print(f"\n{'=' * 60}")
    print("[DONE] PoC workflow completed.")
    print(f"{'=' * 60}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main(repo: str, issue_id: str, branch_name: str):
    state = setup(repo, issue_id, branch_name)

    step = 0
    while True:
        next_node_name = get_next_node(state)
        if next_node_name == "END":
            print(f"\n[MAIN] Reached END (from={state.from_node}, status={state.status})")
            break

        step += 1
        print(f"\n{'─' * 60}")
        print(f"[MAIN] Step {step}: {next_node_name}")
        print(f"  from={state.from_node}  status={state.status}")
        print(f"{'─' * 60}")

        # Run node
        node = NODE_MAP[next_node_name](model=COPILOT_MODEL)
        state = node.run(state)
        print(f"  → Result: status={state.status}")

        # Comment to issue (main's responsibility)
        comment_to_issue(state)

        # Git commit (main's responsibility)
        git_commit(state)

    teardown(state)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main_poc.py <repo> <issue_id> <branch_name>")
        print("Example: python main_poc.py FATESAIKOU/SelfImprovement 20 technical-investigation")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3])
