"""
Node 5: Review Code — 審查程式碼品質與 scope 覆蓋。
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node5ReviewCode(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_5_review_code"
        self.role = "程式碼審查員"
        self.targets = [
            "檢查程式碼是否符合 scope、結構、可讀性、可執行性",
            "檢查 README 是否足夠讓使用者執行",
            "輸出的最後一行必須是狀態行，格式為 STATUS: SUCCESS 或 STATUS: NG",
        ]
        self.constraints = [
            "輸出必須使用以下 markdown 結構：",
            "# Code Review Result",
            "## Scope Coverage",
            "## Code Quality Findings",
            "## Required Fixes（若 NG 才需要填寫）",
            "## README Findings",
            "## Status（最後一行必須是 STATUS: SUCCESS 或 STATUS: NG）",
            "",
            "審查 rubric（每項都必須檢查）：",
            "- 是否覆蓋 scope 中的所有 functional requirements",
            "- 是否有明顯未完成 stub 或 placeholder",
            "- README 是否足夠執行",
            "- 專案結構是否合理",
            "- 是否有不必要過度設計",
        ]

    def run(self, state: State) -> State:
        new_state = state.clone()
        new_state.from_node = self.node_name
        new_state.status = "UNKNOWN"

        prompt = self.build_prompt(
            state.issue_title,
            state.issue_body,
            state.issue_comments,
            state.workflow_output_histories,
        )
        new_state.workflow_input_histories.append((self.node_name, prompt))

        self.log_node("Calling LLM for code review...")
        output, success = self.call_llm(prompt)

        if success:
            if "STATUS: SUCCESS" in output:
                new_state.status = "SUCCESS"
            elif "STATUS: NG" in output:
                new_state.status = "NG"
            else:
                new_state.status = "UNKNOWN"
            self.log_node(f"Review result: {new_state.status} ({len(output)} chars)")
        else:
            new_state.status = "ERROR"
            self.log_node(f"LLM call failed: {output[:200]}")

        new_state.workflow_output_histories.append((self.node_name, output))
        return new_state
