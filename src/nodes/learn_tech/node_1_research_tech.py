"""
Node 1: Research Tech — 根據 issue 主題整理相關技術。
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node1ResearchTech(NodeBase):
    def __init__(self, model: str = "gpt-5-mini", **kwargs):
        super().__init__(model=model, **kwargs)
        self.node_name = "node_1_research_tech"
        self.role = "技術調查員"
        self.targets = [
            "根據 issue 主題，整理相關技術、做法、候選方案、風險與建議方向",
        ]
        self.constraints = [
            "輸出必須使用以下 markdown 結構：",
            "# Tech Research Result",
            "## Problem Understanding",
            "## Candidate Technologies / Approaches（至少列出 3 個候選方案）",
            "## Comparison（表格：Option / Pros / Cons / Complexity / Fitness for MVP）",
            "## Recommended Direction",
            "## Risks",
            "## Assumptions",
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

        self.log_node("Calling LLM for tech research...")
        output, success = self.call_llm(prompt)

        if success:
            new_state.status = "SUCCESS"
            self.log_node(f"LLM returned {len(output)} chars")
        else:
            new_state.status = "ERROR"
            self.log_node(f"LLM call failed: {output[:200]}")

        new_state.workflow_output_histories.append((self.node_name, output))
        return new_state
