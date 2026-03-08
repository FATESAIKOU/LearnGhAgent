"""Port interface for AI agent execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domain.models import AgentResult


class AgentPort(Protocol):
    """Interface for running an AI agent."""

    def run(
        self,
        prompt: str,
        role: str,
        agents_dir: str,
        timeout: int,
        model: str,
        extra_flags: str,
    ) -> AgentResult:
        """Run the agent and return its result."""
        ...
