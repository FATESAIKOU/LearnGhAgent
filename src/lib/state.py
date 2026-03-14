"""
State: workflow 的狀態資料結構。

職責：
  - State 結構定義
  - state clone (deep copy)
  - state append helper

不做：
  - prompt build
  - LLM call
  - git / github 操作
"""

import copy
from dataclasses import dataclass, field


@dataclass
class State:
    # Issue / Repo 基本情報
    issue_id: int = 0
    branch_name: str = ""
    repo: str = ""                  # e.g. "FATESAIKOU/SelfImprovement"
    local_repo_path: str = ""

    # Issue 內容（setup 時從 GitHub 讀取）
    issue_title: str = ""
    issue_body: str = ""
    issue_comments: list = field(default_factory=list)

    # 狀態轉移相關
    from_node: str = "START"
    status: str = "SUCCESS"         # SUCCESS / NG / ERROR / UNKNOWN

    # Workflow 歷史紀錄
    workflow_input_histories: list = field(default_factory=list)   # [(node_name, input_prompt)]
    workflow_output_histories: list = field(default_factory=list)  # [(node_name, output)]

    # 重試計數: key=(from_node, status), value=count
    retry_per_edge_cnt: dict = field(default_factory=dict)

    def clone(self) -> "State":
        """Deep copy state for safe modification in node."""
        return copy.deepcopy(self)
