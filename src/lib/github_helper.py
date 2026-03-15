"""
GithubHelper: GitHub 操作 helper。

職責：
  - 讀 issue (title, body, comments)
  - 寫 comment（將 state 中與審查有關內容轉成漂亮 markdown）

不做：
  - 決定節點邏輯
  - 決定 status
  - 直接操作 git
"""

import json
import subprocess


class GithubHelper:
    """GitHub CLI wrapper for issue operations."""

    @staticmethod
    def _run_gh(args: list[str]) -> subprocess.CompletedProcess:
        """Run gh CLI command."""
        display = " ".join(args[:6])
        if len(args) > 6:
            display += "..."
        print(f"  [GH] {display}")
        return subprocess.run(args, capture_output=True, text=True)

    @staticmethod
    def read_issue(repo: str, issue_id: int) -> tuple[str, str, list[str]]:
        """Read issue from GitHub. Returns (title, body, comments)."""
        r = GithubHelper._run_gh([
            "gh", "issue", "view", str(issue_id),
            "--repo", repo,
            "--json", "title,body,comments",
        ])

        if r.returncode != 0:
            print(f"  ❌ Read issue FAILED: {r.stderr.strip()}")
            return "", "", []

        try:
            data = json.loads(r.stdout)
            title = data.get("title", "")
            body = data.get("body", "")
            comments = [c.get("body", "") for c in data.get("comments", [])]
            print(f"  ✅ Issue: {title}")
            return title, body, comments
        except json.JSONDecodeError:
            print(f"  ⚠️  Failed to parse issue JSON")
            return "", "", []

    @staticmethod
    def comment_to_issue(repo: str, issue_id: int, state) -> None:
        """Post formatted workflow update comment to issue.

        Format follows architect_principle.md template:
          ## Workflow Update - {node_name}
          - Status / Issue / Branch metadata
          - Input summary (collapsible)
          - Full output
        """
        if not state.workflow_output_histories:
            return

        node_name, output = state.workflow_output_histories[-1]

        # Input summary (collapsible)
        input_summary = "(no input)"
        if state.workflow_input_histories:
            _, last_input = state.workflow_input_histories[-1]
            input_summary = last_input[:2000]
            if len(last_input) > 2000:
                input_summary += "\n...(truncated)"

        # Truncate output for GitHub comment limit (65536 chars)
        output_display = output[:58000]
        if len(output) > 58000:
            output_display += "\n\n...(truncated)"

        comment_body = (
            f"## Workflow Update - `{node_name}`\n\n"
            f"- **Status**: `{state.status}`\n"
            f"- **Issue**: #{issue_id}\n"
            f"- **Branch**: `{state.branch_name}`\n\n"
            f"<details>\n"
            f"<summary>Input (click to expand)</summary>\n\n"
            f"```\n{input_summary}\n```\n\n"
            f"</details>\n\n"
            f"### Output\n\n"
            f"{output_display}\n\n"
            f"---\n"
            f"_Posted by LearnTech Workflow_"
        )

        print(f"  [COMMENT] Posting for {node_name}...")
        GithubHelper._run_gh([
            "gh", "issue", "comment", str(issue_id),
            "--repo", repo,
            "--body", comment_body,
        ])
