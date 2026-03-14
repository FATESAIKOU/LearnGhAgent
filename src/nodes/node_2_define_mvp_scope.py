"""
Node 2: Define MVP Scope — 根據技術調查結果收斂 MVP 邊界。

職責：
  - 組裝 prompt（MVP scope 定義）
  - 呼叫 LLM
  - 解析輸出
  - 判定 status

不做：
  - 決定下一個節點
  - 直接 git / github 操作
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node2DefineMvpScope(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_2_define_mvp_scope"
        self.role = "MVP 設計師"
        self.targets = [
            "根據技術調查結果，收斂 MVP 邊界、功能、非功能需求、驗收條件",
        ]
        self.constraints = [
            "輸出必須使用以下 markdown 結構：",
            "# MVP Scope Definition",
            "## Goal",
            "## In Scope",
            "## Out of Scope",
            "## Functional Requirements",
            "## Non-Functional Requirements",
            "## Acceptance Criteria（必須是可驗證的條件）",
            "## Implementation Notes",
        ]

    EXPECTED_HEADERS = [
        "Goal",
        "In Scope",
        "Out of Scope",
        "Functional Requirements",
        "Acceptance Criteria",
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

        self.log_node("Calling LLM for MVP scope definition...")
        output, success = self.call_llm(prompt)

        if success:
            if self._has_expected_headers(output, self.EXPECTED_HEADERS, min_matches=3):
                new_state.status = "SUCCESS"
            else:
                new_state.status = "UNKNOWN"
            self.log_node(f"LLM returned {len(output)} chars, status={new_state.status}")
        else:
            new_state.status = "ERROR"
            self.log_node(f"LLM call failed: {output[:200]}")

        new_state.workflow_output_histories.append((self.node_name, output))
        return new_state
