"""
Node 1: Hello LLM — 呼叫 gh copilot 驗證 LLM 連線。

職責：
  - 組裝 prompt（用一句話概括 issue 主題）
  - 呼叫 gh copilot
  - 解析輸出
  - 判定 status

不做：
  - 決定下一個節點
  - 直接 git / github 操作
"""

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node1HelloLlm(NodeBase):
    def __init__(self):
        super().__init__()
        self.node_name = "node_1_hello_llm"
        self.role = "技術摘要助手"
        self.targets = ["用一句話概括這個 issue 的主題"]
        self.constraints = ["只輸出一句話，不超過 100 字"]

    def run(self, state: State) -> State:
        new_state = state.clone()
        new_state.from_node = self.node_name
        new_state.status = "UNKNOWN"

        # Build prompt
        prompt = self.build_prompt(
            state.issue_title,
            state.issue_body,
            state.issue_comments,
            state.workflow_output_histories,
        )
        new_state.workflow_input_histories.append((self.node_name, prompt))

        self.log_node("Calling LLM via gh copilot...")

        # Call LLM
        output, success = self.call_llm(prompt)

        if success:
            new_state.status = "SUCCESS"
            self.log_node(f"LLM returned: {output[:200]}")
        else:
            new_state.status = "UNKNOWN"
            self.log_node(f"LLM call did not succeed: {output[:200]}")

        new_state.workflow_output_histories.append((self.node_name, output))
        return new_state
