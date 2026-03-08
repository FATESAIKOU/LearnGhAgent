"""Hooks adapter — implements HooksPort using subprocess."""

import logging
import os
import subprocess

logger = logging.getLogger(__name__)

WORKSPACE_SCRIPTS_DIR = "/app/workspace-scripts"


def _run_cmd(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> str:
    """Run a command and return stdout."""
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


class SubprocessHooksAdapter:
    """Implements HooksPort via subprocess execution of shell scripts."""

    def __init__(self, scripts_dir: str = WORKSPACE_SCRIPTS_DIR):
        self.scripts_dir = scripts_dir

    def run_workspace_scripts(self, script_names: list[str]) -> bool:
        """Execute a list of workspace scripts sequentially.

        Returns True if all scripts succeeded, False if any failed.
        On failure, logs the error but continues with remaining scripts.
        """
        if not script_names:
            return True

        all_ok = True
        for name in script_names:
            script_path = os.path.join(self.scripts_dir, name)
            if not os.path.isfile(script_path):
                logger.error("Workspace script not found: %s", script_path)
                all_ok = False
                continue

            logger.info("Running workspace script: %s", name)
            try:
                _run_cmd(["bash", script_path], timeout=60)
            except Exception as e:
                logger.error("Workspace script '%s' failed: %s", name, e)
                all_ok = False

        return all_ok
