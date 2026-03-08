"""Port interface for Git workspace operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domain.workflow import RepoConfig


class GitPort(Protocol):
    """Interface for Git workspace management (clone, branch, push, PR)."""

    def init_workspace(self, repos: list[RepoConfig], issue_number: int) -> None:
        """Clone repos and create/checkout feature branches."""
        ...

    def push_workspace(
        self,
        repos: list[RepoConfig],
        issue_number: int,
        issue_repo: str,
        phase_name: str,
    ) -> None:
        """Stage, commit, push changes and create draft PRs."""
        ...
