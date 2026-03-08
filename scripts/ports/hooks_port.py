"""Port interface for workspace hook scripts."""

from typing import Protocol


class HooksPort(Protocol):
    """Interface for executing workspace hook scripts."""

    def run_workspace_scripts(self, script_names: list[str]) -> bool:
        """Execute a list of workspace scripts sequentially.

        Returns True if all scripts succeeded, False if any failed.
        """
        ...
