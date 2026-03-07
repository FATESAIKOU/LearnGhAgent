"""State persistence — read/write state.json."""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, state_file: str):
        self._path = Path(state_file)
        self._state: dict = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load state file: %s", e)
                return {"issues": {}}
        return {"issues": {}}

    def _save(self) -> None:
        # Write to temp then rename for atomicity
        tmp_path = self._path.with_suffix(".tmp")
        try:
            os.makedirs(self._path.parent, exist_ok=True)
            with open(tmp_path, "w") as f:
                json.dump(self._state, f, indent=2)
            tmp_path.rename(self._path)
        except OSError as e:
            logger.error("Failed to save state file: %s", e)
            raise

    def get_last_processed(self, issue_number: int) -> str:
        """Return last_processed_at for an issue, or empty string."""
        key = str(issue_number)
        return self._state.get("issues", {}).get(key, {}).get("last_processed_at", "")

    def update_last_processed(self, issue_number: int, timestamp: str) -> None:
        """Update last_processed_at for an issue and persist."""
        key = str(issue_number)
        if "issues" not in self._state:
            self._state["issues"] = {}
        self._state["issues"][key] = {"last_processed_at": timestamp}
        self._save()
        logger.info("Issue #%d: state updated to %s", issue_number, timestamp)
