"""
Node 3: Review MVP Scope — 審查 MVP scope 是否合理。
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node3ReviewMvpScope(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_3_review_mvp_scope"
        self.role = "MVP 審查員"
        self.targets = [
            "檢查 MVP scope 是否過大、過小、不一致、不可實作、驗收條件不足",
            "輸出的第一行必須是判定結果：STATUS: SUCCESS 或 STATUS: NG",
        ]
        self.constraints = [
            "第一行必須是 STATUS: SUCCESS 或 STATUS: NG（二擇一）",
            "後續輸出必須使用以下 markdown 結構：",
            "# MVP Scope Review",
            "## Findings",
            "## Missing / Over-scoped / Inconsistent Points",
            "## Required Fixes（若 NG 才需要填寫）",
            "",
            "審查 rubric（每項都必須檢查）：",
            "- 是否明確對應 issue 目標",
            "- 是否可在 MVP 時間/規模內完成",
            "- in-scope / out-of-scope 是否清楚",
            "- acceptance criteria 是否可驗證",
            "- 是否與技術調查結論一致",
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

        self.log_node("Calling LLM for MVP scope review...")
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
