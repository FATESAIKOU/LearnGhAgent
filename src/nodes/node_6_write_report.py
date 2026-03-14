"""
Node 6: Write Report — 撰寫開發報告以及程式碼內容報告。

職責：
  - 組裝 prompt（報告撰寫）
  - 呼叫 LLM
  - 解析輸出
  - 判定 status

不做：
  - 決定下一個節點
  - 直接 git / github 操作
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node6WriteReport(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_6_write_report"
        self.role = "開發報告撰寫員"
        self.targets = [
            "將研究、scope、實作、使用方式、限制與後續方向整理成完整的開發報告",
        ]
        self.constraints = [
            "輸出必須使用以下 markdown 結構：",
            "# Development Report",
            "## What Was Researched",
            "## Chosen MVP Scope",
            "## What Was Implemented",
            "## How to Run",
            "## Known Limitations",
            "## Next Steps",
        ]

    EXPECTED_HEADERS = [
        "What Was Researched",
        "Chosen MVP Scope",
        "What Was Implemented",
        "How to Run",
        "Known Limitations",
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

        self.log_node("Calling LLM to write report...")
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
