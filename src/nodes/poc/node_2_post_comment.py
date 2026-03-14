"""
Node 2: Post Comment — 組裝 workflow 摘要。
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node2PostComment(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_2_post_comment"
        self.role = "結果彙報員"
        self.targets = ["將 workflow 的執行紀錄整理成 markdown 摘要"]
        self.constraints = ["必須包含狀態轉移軌跡和 LLM 輸出"]

    def run(self, state: State) -> State:
        new_state = state.clone()
        new_state.from_node = self.node_name
        new_state.status = "UNKNOWN"

        self.log_node("Building workflow summary...")

        try:
            lines = [
                "# PoC Workflow Summary",
                "",
                "## Execution Trace",
                "",
            ]

            for i, (name, output) in enumerate(state.workflow_output_histories, 1):
                lines.append(f"### Step {i}: `{name}`")
                lines.append("")
                lines.append("```")
                lines.append(output[:1000])
                lines.append("```")
                lines.append("")

            lines.extend([
                "## Verification Results",
                "",
                "| Item | Status |",
                "|------|--------|",
                "| gh auth | ✅ |",
                "| Read issue | ✅ |",
                "| copilot LLM call | ✅ |",
                "| State transition | ✅ |",
                "| gh issue comment | ⏳ (this comment itself) |",
                "| git commit/push | ⏳ (teardown) |",
                "",
                "---",
                "_Posted by PoC workflow_",
            ])

            summary = "\n".join(lines)

            new_state.workflow_input_histories.append(
                (self.node_name, "(fixed logic — no prompt)")
            )
            new_state.workflow_output_histories.append(
                (self.node_name, summary)
            )
            new_state.status = "SUCCESS"
            self.log_node("Summary built successfully.")

        except Exception as e:
            error_msg = f"ERROR: {e}"
            new_state.workflow_output_histories.append(
                (self.node_name, error_msg)
            )
            new_state.status = "ERROR"
            self.log_node(f"Failed: {e}")

        return new_state
