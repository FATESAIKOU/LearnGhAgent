"""
NodeBase: 所有 workflow node 的抽象基底類別。

職責：
  - node metadata (node_name, role, targets, constraints)
  - build_prompt() 共通骨架
  - run(state) 介面定義
  - 共通 logging helper

不做：
  - 決定 workflow transition
  - 直接操作 git / github
  - 決定整體 orchestration
"""

import os
import subprocess
import tempfile
from abc import ABC, abstractmethod

from src.lib.state import State


class NodeBase(ABC):
    def __init__(self, model: str = "gpt-5-mini"):
        self.node_name: str = ""
        self.role: str = ""
        self.targets: list[str] = []
        self.constraints: list[str] = []
        self.model: str = model

    def build_prompt(
        self,
        issue_title: str,
        issue_body: str,
        issue_comments: list[str],
        workflow_output_histories: list[tuple[str, str]],
    ) -> str:
        """Build the standard prompt structure shared by all nodes."""
        # Comments
        if issue_comments:
            comments_str = "\n".join(
                f"        - {c[:300]}" for c in issue_comments
            )
        else:
            comments_str = "        (none)"

        # Workflow progress
        if workflow_output_histories:
            histories_str = "\n".join(
                f"        - [{name}]: {output[:500]}"
                for name, output in workflow_output_histories
            )
        else:
            histories_str = "        (none)"

        # Targets / Constraints
        targets_str = "\n".join(f"            - {t}" for t in self.targets)
        constraints_str = "\n".join(f"            - {c}" for c in self.constraints)

        return f"""- issue
    - title: {issue_title}
    - body: {issue_body[:1000]}
    - comments
{comments_str}
- workflow_progress
{histories_str}
- node_instructions
    - role: {self.role}
    - targets
{targets_str}
    - constraints
{constraints_str}"""

    def call_llm(self, prompt: str) -> tuple[str, bool]:
        """
        Call LLM via copilot CLI (npm: @github/copilot).
        Model is determined by self.model (set from main's global constant).
        Returns (output_text, success_flag).
        """
        model = self.model
        prompt_path = None
        try:
            # Write prompt to temp file to avoid shell escaping issues
            fd, prompt_path = tempfile.mkstemp(suffix=".md", prefix="poc_prompt_")
            with os.fdopen(fd, "w") as f:
                f.write(prompt)

            cmd = [
                "copilot",
                "--model", model,
                "-p", f"@{prompt_path}",
                "--allow-all-tools",
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
        finally:
            if prompt_path and os.path.exists(prompt_path):
                os.unlink(prompt_path)

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
