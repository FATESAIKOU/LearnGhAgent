"""
Node 4: Implement MVP — 依 scope 實作 MVP 程式碼與專案檔案。
"""

import os
import re

from src.nodes.node_base import NodeBase
from src.lib.state import State


class Node4ImplementMvp(NodeBase):
    def __init__(self, model: str = "gpt-5-mini"):
        super().__init__(model=model)
        self.node_name = "node_4_implement_mvp"
        self.role = "MVP 開發者"
        self.targets = [
            "依照已審查通過的 MVP scope 實作程式碼與基本專案檔案",
            "必須包含 README.md 說明如何執行",
        ]
        self.constraints = [
            "必須實際輸出 MVP 程式碼與 README.md",
            "每個檔案必須使用以下格式輸出：",
            "--- FILE: relative/path/to/file.ext ---",
            "(file content)",
            "--- END FILE ---",
            "使用相對路徑（如 src/main.py, README.md）",
            "程式碼必須可直接執行，不得有 placeholder 或 TODO stub",
            "必須包含 README.md 說明如何執行",
        ]

    def _parse_and_write_files(self, output: str, base_path: str) -> int:
        """Parse file blocks from LLM output and write to disk.
        Returns number of files written.
        """
        pattern = re.compile(
            r'--- FILE:\s*(.+?)\s*---\n(.*?)--- END FILE ---',
            re.DOTALL,
        )
        matches = pattern.findall(output)

        count = 0
        for filepath, content in matches:
            filepath = filepath.strip()

            # Security: prevent path traversal
            if '..' in filepath or filepath.startswith('/'):
                self.log_node(f"  Skipping suspicious path: {filepath}")
                continue

            full_path = os.path.join(base_path, filepath)
            os.makedirs(os.path.dirname(full_path) if os.path.dirname(full_path) else base_path, exist_ok=True)

            with open(full_path, 'w') as f:
                f.write(content)

            self.log_node(f"  Written: {filepath}")
            count += 1

        return count

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

        self.log_node("Calling LLM for MVP implementation...")
        output, success = self.call_llm(prompt)

        if success:
            files_written = self._parse_and_write_files(output, state.local_repo_path)
            self.log_node(f"Files written: {files_written}")
            new_state.status = "SUCCESS"
            self.log_node(f"LLM returned {len(output)} chars")
        else:
            new_state.status = "ERROR"
            self.log_node(f"LLM call failed: {output[:200]}")

        new_state.workflow_output_histories.append((self.node_name, output))
        return new_state
