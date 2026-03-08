"""Workflow domain models — pure data structures for workflow definitions."""

from dataclasses import dataclass, field


@dataclass
class RepoConfig:
    """A repo definition from the workflow config section."""
    repo: str          # owner/repo format (e.g. "FATESAIKOU/SomeProject")
    url: str = ""      # optional git URL override (if empty, uses ``gh repo clone``)
    description: str = ""


@dataclass
class Phase:
    """A single phase in a workflow."""
    role: str
    phasename: str
    phasetarget: str = ""
    llm_model: str = ""
    extra_flags: str = ""
    workspace_init: list[str] = field(default_factory=list)
    workspace_cleanup: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    """A workflow definition containing phases and repo configurations."""
    name: str
    repos: list[RepoConfig] = field(default_factory=list)
    phases: list[Phase] = field(default_factory=list)
