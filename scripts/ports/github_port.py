"""Port interface for GitHub operations."""

from __future__ import annotations

from typing import Any, Protocol


class GitHubPort(Protocol):
    """Interface for GitHub API operations.

    All ``repo`` parameters use ``owner/repo`` format.
    """

    def list_open_issues(self, repo: str) -> list[dict[str, Any]]: ...

    def get_issue(self, repo: str, number: int) -> dict[str, Any]: ...

    def get_issue_comments(self, repo: str, number: int) -> list[dict[str, Any]]: ...

    def post_comment(self, repo: str, number: int, body: str) -> None: ...

    def add_label(self, repo: str, number: int, label: str) -> None: ...

    def remove_label(self, repo: str, number: int, label: str) -> None: ...
