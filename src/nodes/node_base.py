"""
NodeBase: 所有 workflow node 的抽象基底類別。

職責：
  - node metadata (node_name, role, targets, constraints)
  - build_prompt() 共通骨架（JSON 格式）
  - call_llm() 呼叫 copilot CLI
  - run(state) 介面定義
  - 共通 logging helper

不做：
  - 決定 workflow transition
  - 直接操作 git / github
  - 決定整體 orchestration
  - 判定 status（交給各 node 自行 keyword matching）
"""

import json
import subprocess
from abc import ABC, abstractmethod

from src.lib.state import State


class NodeBase(ABC):
    def __init__(self, model: str = "gpt-5-mini", history_keep_full: int = 3):
        self.node_name: str = ""
        self.role: str = ""
        self.targets: list[str] = []
        self.constraints: list[str] = []
        self.model: str = model
        self.history_keep_full: int = history_keep_full

    def _build_workflow_progress(
        self, histories: list[tuple[str, str]]
    ) -> list[dict]:
        """Build workflow_progress list.

        The most recent ``self.history_keep_full`` entries are included in
        full.  Older entries are truncated to 500 chars so the prompt
        doesn't explode while still preserving the recent context that
        matters most (e.g. reviewer feedback the next node needs to see).
        """
        if not histories:
            return []

        keep = self.history_keep_full
        result: list[dict] = []
        cutoff = max(len(histories) - keep, 0)
        for i, (name, output) in enumerate(histories):
            if i < cutoff:
                result.append({"node": name, "output": output[:500]})
            else:
                result.append({"node": name, "output": output})
        return result

    def build_prompt(
        self,
        issue_title: str,
        issue_body: str,
        issue_comments: list[str],
        workflow_output_histories: list[tuple[str, str]],
    ) -> str:
        """Build the standard prompt as a JSON string.

        Free-text fields are json.dumps()-ed so that newlines become \\n
        and won't break the overall prompt structure.
        """
        prompt_obj = {
            "issue": {
                "title": issue_title,
                "body": issue_body[:1000],
                "comments": [c[:300] for c in issue_comments] if issue_comments else [],
            },
            "workflow_progress": self._build_workflow_progress(workflow_output_histories),
            "node_instructions": {
                "role": self.role,
                "targets": self.targets,
                "constraints": self.constraints,
            },
        }
        return json.dumps(prompt_obj, ensure_ascii=False, indent=2)

    def call_llm(self, prompt: str) -> tuple[str, bool]:
        """
        Call LLM via copilot CLI (npm: @github/copilot).
        Model is determined by self.model (set from main's global constant).
        Returns (output_text, success_flag).
        """
        model = self.model
        try:
            cmd = [
                "copilot",
                "--model", model,
                "-p", prompt,
                "--no-ask-user",
            ]
            self.log_node(f"LLM model: {model}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode == 0 and stdout:
                return stdout, True
            else:
                return (
                    f"[LLM FAILED] rc={result.returncode}\n"
                    f"stdout={stdout[:500]}\n"
                    f"stderr={stderr[:500]}"
                ), False

        except subprocess.TimeoutExpired:
            return "[LLM TIMEOUT]", False
        except Exception as e:
            return f"[LLM EXCEPTION] {e}", False

    def log_node(self, message: str):
        """Shared logging helper for nodes."""
        print(f"  [{self.node_name}] {message}")

    @abstractmethod
    def run(self, state: State) -> State:
        """
        Execute this node's logic.
        Must return a new State with:
          - from_node = self.node_name
          - status = SUCCESS / NG / ERROR / UNKNOWN
          - workflow_input_histories appended
          - workflow_output_histories appended
        """
        pass
