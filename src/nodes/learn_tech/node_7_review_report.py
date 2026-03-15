"""
Node 7: Review Report — 審查報告完整性與一致性。
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node7ReviewReport(NodeBase):
    def __init__(self, model: str = "gpt-5-mini", **kwargs):
        super().__init__(model=model, **kwargs)
        self.node_name = "node_7_review_report"
        self.role = "報告審查員"
        self.targets = [
            "檢查報告是否完整、與程式碼一致、是否足夠讓人審查與接手",
            "輸出的第一行必須是判定結果：STATUS: SUCCESS 或 STATUS: NG",
        ]
        self.constraints = [
            "第一行必須是 STATUS: SUCCESS 或 STATUS: NG（二擇一）",
            "後續輸出必須使用以下 markdown 結構：",
            "# Report Review Result",
            "## Completeness Check",
            "## Consistency Check",
            "## Missing Information",
            "## Required Fixes（若 NG 才需要填寫）",
            "",
            "審查 rubric（每項都必須檢查）：",
            "- 是否完整描述研究、scope、實作、限制",
            "- 是否與實際程式碼一致",
            "- 是否足夠讓第三者理解",
            "- 是否能支持後續擴充或重做",
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

        self.log_node("Calling LLM for report review...")
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
