"""Port interface for workspace hook scripts."""

from typing import Protocol


class HooksPort(Protocol):
    """Interface for executing workspace hook scripts."""

    def run_workspace_scripts(
        self,
        script_names: list[str],
        phase_env: dict[str, str] | None = None,
    ) -> bool:
        """Execute a list of workspace scripts sequentially.

        Args:
            script_names: List of script filenames to run.
            phase_env: Extra environment variables passed to each script.

        Returns True if all scripts succeeded, False if any failed.
        """
        ...
