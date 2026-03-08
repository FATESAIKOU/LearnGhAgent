"""Workflow loader — parse workflow YAML and resolve phase transitions."""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# PyYAML is not in stdlib; use a minimal parser or require it.
# We'll use a simple approach: try import yaml, fallback to manual parse.
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class RepoConfig:
    """A repo definition from the workflow ``config`` section."""
    repo: str          # owner/repo format (e.g. "FATESAIKOU/SomeProject")
    url: str = ""      # optional git URL override (if empty, uses ``gh repo clone``)
    description: str = ""


@dataclass
class Phase:
    role: str
    phasename: str
    phasetarget: str = ""
    llm_model: str = ""
    extra_flags: str = ""
    workspace_init: list[str] = field(default_factory=list)
    workspace_cleanup: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    name: str
    repos: list[RepoConfig] = field(default_factory=list)
    phases: list[Phase] = field(default_factory=list)


def _parse_yaml(path: str) -> dict[str, Any]:
    """Parse a YAML file. Uses PyYAML if available, otherwise json fallback."""
    if yaml is not None:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        # Minimal fallback: try json (won't work for real YAML)
        import json
        with open(path, "r") as f:
            return json.load(f)


def _parse_repos(raw_list: list[dict[str, Any]]) -> list[RepoConfig]:
    """Parse the ``config`` list into RepoConfig objects."""
    repos: list[RepoConfig] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        repos.append(RepoConfig(
            repo=item.get("repo", ""),
            url=item.get("url", ""),
            description=item.get("description", ""),
        ))
    return repos


def _parse_phases(raw_list: list[dict[str, Any]]) -> list[Phase]:
    """Parse a list of phase dicts into Phase objects."""
    phases: list[Phase] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        phases.append(Phase(
            role=item.get("role", ""),
            phasename=item.get("phasename", ""),
            phasetarget=item.get("phasetarget", ""),
            llm_model=item.get("llm-model", ""),
            extra_flags=item.get("extra-flags", ""),
            workspace_init=item.get("workspace-init", []) or [],
            workspace_cleanup=item.get("workspace-cleanup", []) or [],
        ))
    return phases


def load_workflows(workflow_file: str) -> dict[str, Workflow]:
    """Load all workflows from a YAML file.

    Supports two formats:

    **New format (config + steps):**

        workflowA:
          config:
            - repo: owner/repo
              url: ""
              description: "some project"
          steps:
            - role: manager
              phasename: requirement-analysis
              phasetarget: "produce requirements doc"
              llm-model: ""
              extra-flags: ""

    **Legacy format (flat list of phases):**

        workflowA:
          - role: manager
            phasename: requirement-analysis
            ...
    """
    if not workflow_file or not os.path.isfile(workflow_file):
        logger.info("No workflow file found at '%s', workflow features disabled", workflow_file)
        return {}

    try:
        raw = _parse_yaml(workflow_file)
    except Exception as e:
        logger.error("Failed to parse workflow file '%s': %s", workflow_file, e)
        return {}

    workflows: dict[str, Workflow] = {}
    for wf_name, wf_data in raw.items():
        if isinstance(wf_data, list):
            # Legacy format: flat list of phases, no repos
            phases = _parse_phases(wf_data)
            repos: list[RepoConfig] = []
        elif isinstance(wf_data, dict):
            # New format: config (repos) + steps (phases)
            repos = _parse_repos(wf_data.get("config", []) or [])
            phases = _parse_phases(wf_data.get("steps", []) or [])
        else:
            logger.warning("Workflow '%s' has unexpected type, skipping", wf_name)
            continue

        workflows[wf_name] = Workflow(name=wf_name, repos=repos, phases=phases)
        logger.info(
            "Loaded workflow '%s' with %d repos, %d phases",
            wf_name, len(repos), len(phases),
        )

    return workflows


def find_current_phase(workflow: Workflow, current_role: str) -> Optional[int]:
    """Find the index of the current phase by role name.

    If the same role appears multiple times, we match the first one
    whose role matches. The caller should use label-based disambiguation
    if needed (e.g. workflow:name:phasename).
    """
    for i, phase in enumerate(workflow.phases):
        if phase.role == current_role:
            return i
    return None


def find_phase_by_label(workflow: Workflow, phase_label: str) -> Optional[int]:
    """Find phase index by the full label 'workflow:<wf_name>:<phasename>'.

    The phase_label passed here is just the phasename part.
    """
    for i, phase in enumerate(workflow.phases):
        if phase.phasename == phase_label:
            return i
    return None


def get_next_phase(workflow: Workflow, current_index: int) -> Optional[Phase]:
    """Return the next phase after current_index, or None if it's the last."""
    next_idx = current_index + 1
    if next_idx < len(workflow.phases):
        return workflow.phases[next_idx]
    return None
