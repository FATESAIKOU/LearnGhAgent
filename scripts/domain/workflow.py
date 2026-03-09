"""Workflow domain models — pure data structures for workflow definitions."""

from dataclasses import dataclass, field


@dataclass
class RepoConfig:
    """A repo definition from the workflow config section."""
    repo: str          # owner/repo format (e.g. "FATESAIKOU/SomeProject")
    url: str = ""      # optional git URL override (if empty, uses ``gh repo clone``)
    description: str = ""


@dataclass
class BranchRule:
    """A single branching rule evaluated after phase completion.

    ``conditions`` is a dict of KEY=VALUE pairs matched against the branch-vars
    file written by workspace-cleanup scripts.  A rule with an empty
    ``conditions`` dict is an unconditional default (always matches).
    """
    target: str                                        # phasename or "end"
    conditions: dict[str, str] = field(default_factory=dict)


@dataclass
class Phase:
    """A single phase in a workflow."""
    role: str
    phasename: str
    phase_prompt: str = ""
    llm_model: str = ""
    workspace_init: list[str] = field(default_factory=list)
    workspace_cleanup: list[str] = field(default_factory=list)
    phase_env: dict[str, str] = field(default_factory=dict)
    branchs: list[BranchRule] = field(default_factory=list)


@dataclass
class Workflow:
    """A workflow definition containing phases and repo configurations."""
    name: str
    repos: list[RepoConfig] = field(default_factory=list)
    phases: list[Phase] = field(default_factory=list)
