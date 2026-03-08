"""Domain models — pure data structures with zero dependencies."""

from dataclasses import dataclass


@dataclass
class AgentResult:
    """Result of running an AI agent."""
    exit_code: int
    output: str
    timed_out: bool


@dataclass
class ResolvedLabels:
    """Result of label resolution from an issue."""
    role: str           # Active role name (empty if none matched)
    role_label: str     # The full label string e.g. "role:manager"
    workflow_name: str  # From "workflow:xxx" label (empty if none)
    phase_name: str     # From "phase:xxx" label (empty if none)
