"""
main_learn_tech.py: 先端技術研究 workflow orchestration。

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

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lib.state import State
from src.lib.github_helper import GithubHelper
from src.lib.git_helper import GitHelper
from src.nodes.learn_tech.node_1_research_tech import Node1ResearchTech
from src.nodes.learn_tech.node_2_define_mvp_scope import Node2DefineMvpScope
from src.nodes.learn_tech.node_3_review_mvp_scope import Node3ReviewMvpScope
from src.nodes.learn_tech.node_4_implement_mvp import Node4ImplementMvp
from src.nodes.learn_tech.node_5_review_code import Node5ReviewCode
from src.nodes.learn_tech.node_6_write_report import Node6WriteReport
from src.nodes.learn_tech.node_7_review_report import Node7ReviewReport


# ──────────────────────────────────────────────
# Global Constants
# ──────────────────────────────────────────────

COPILOT_MODEL = os.environ.get("COPILOT_MODEL", "gpt-5-mini")


# ──────────────────────────────────────────────
# Transfer Matrix (from workflow_spec.md)
# ──────────────────────────────────────────────

TRANSFER_MATRIX = {
    ("START", "SUCCESS"):                    "node_1_research_tech",

    ("node_1_research_tech", "SUCCESS"):     "node_2_define_mvp_scope",
    ("node_1_research_tech", "UNKNOWN"):     "node_1_research_tech",
    ("node_1_research_tech", "ERROR"):       "END",

    ("node_2_define_mvp_scope", "SUCCESS"):  "node_3_review_mvp_scope",
    ("node_2_define_mvp_scope", "UNKNOWN"):  "node_2_define_mvp_scope",
    ("node_2_define_mvp_scope", "ERROR"):    "END",

    ("node_3_review_mvp_scope", "SUCCESS"):  "node_4_implement_mvp",
    ("node_3_review_mvp_scope", "NG"):       "node_2_define_mvp_scope",
    ("node_3_review_mvp_scope", "UNKNOWN"):  "node_3_review_mvp_scope",
    ("node_3_review_mvp_scope", "ERROR"):    "END",

    ("node_4_implement_mvp", "SUCCESS"):     "node_5_review_code",
    ("node_4_implement_mvp", "UNKNOWN"):     "node_4_implement_mvp",
    ("node_4_implement_mvp", "ERROR"):       "END",

    ("node_5_review_code", "SUCCESS"):       "node_6_write_report",
    ("node_5_review_code", "NG"):            "node_4_implement_mvp",
    ("node_5_review_code", "UNKNOWN"):       "node_5_review_code",
    ("node_5_review_code", "ERROR"):         "END",

    ("node_6_write_report", "SUCCESS"):      "node_7_review_report",
    ("node_6_write_report", "UNKNOWN"):      "node_6_write_report",
    ("node_6_write_report", "ERROR"):        "END",

    ("node_7_review_report", "SUCCESS"):     "END",
    ("node_7_review_report", "NG"):          "node_6_write_report",
    ("node_7_review_report", "UNKNOWN"):     "node_7_review_report",
    ("node_7_review_report", "ERROR"):       "END",
}

MAX_RETRY = 3  # spec: 同一 edge 超過 3 次 → END

NODE_MAP = {
    "node_1_research_tech":    Node1ResearchTech,
    "node_2_define_mvp_scope": Node2DefineMvpScope,
    "node_3_review_mvp_scope": Node3ReviewMvpScope,
    "node_4_implement_mvp":    Node4ImplementMvp,
    "node_5_review_code":      Node5ReviewCode,
    "node_6_write_report":     Node6WriteReport,
    "node_7_review_report":    Node7ReviewReport,
}


# ──────────────────────────────────────────────
# Orchestration
# ──────────────────────────────────────────────

def get_next_node(state: State) -> str:
    """Look up transfer matrix. Returns 'END' if done or retry exceeded."""
    key = (state.from_node, state.status)
    next_name = TRANSFER_MATRIX.get(key, "END")

    if next_name == "END":
        return "END"

    # Check retry limit (spec: 同一 edge 超過 MAX_RETRY 次 → END)
    retry_count = state.retry_per_edge_cnt.get(key, 0)
    if retry_count >= MAX_RETRY:
        print(f"  [RETRY EXCEEDED] {key} retried {retry_count}/{MAX_RETRY} → END")
        return "END"

    state.retry_per_edge_cnt[key] = retry_count + 1
    return next_name


def setup(repo: str, issue_id: str, branch_name: str) -> State:
    """Clone repo, checkout branch, read issue, initialize state."""
    print("=" * 60)
    print(f"[SETUP] repo={repo} issue=#{issue_id} branch={branch_name}")
    print(f"  model={COPILOT_MODEL}")
    print("=" * 60)

    # 1. Clone & checkout
    print("\n[1/3] Cloning and checking out...")
    local_path = GitHelper.clone_and_checkout(repo, branch_name)

    # 2. Remove origin (safety)
    print("\n[2/3] Removing origin (safety)...")
    GitHelper.remove_origin(local_path)

    # 3. Read issue
    print(f"\n[3/3] Reading issue #{issue_id}...")
    title, body, comments = GithubHelper.read_issue(repo, int(issue_id))

    state = State(
        issue_id=int(issue_id),
        branch_name=branch_name,
        repo=repo,
        local_repo_path=local_path,
        issue_title=title,
        issue_body=body,
        issue_comments=comments,
        from_node="START",
        status="SUCCESS",
    )

    print(f"\n{'=' * 60}")
    print("[SETUP DONE]")
    print(f"{'=' * 60}")
    return state


def teardown(state: State):
    """Add origin back and push."""
    print(f"\n{'=' * 60}")
    print("[TEARDOWN]")
    print(f"{'=' * 60}")

    GitHelper.add_origin_and_push(state.local_repo_path, state.repo, state.branch_name)

    print(f"\n{'=' * 60}")
    print("[DONE] LearnTech workflow completed.")
    print(f"{'=' * 60}")


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
        GithubHelper.comment_to_issue(state.repo, state.issue_id, state)

        # Git commit (main's responsibility)
        GitHelper.commit(state.local_repo_path, state.from_node, state.status)

    teardown(state)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main_learn_tech.py <repo> <issue_id> <branch_name>")
        print("Example: python main_learn_tech.py FATESAIKOU/SelfImprovement 20 technical-investigation")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3])
