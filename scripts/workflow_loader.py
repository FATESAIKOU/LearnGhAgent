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
class Phase:
    role: str
    phasename: str
    phasetarget: str = ""
    llm_model: str = ""
    extra_flags: str = ""


@dataclass
class Workflow:
    name: str
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


def load_workflows(workflow_file: str) -> dict[str, Workflow]:
    """Load all workflows from a YAML file.

    Expected format:
        workflowA:
          - role: manager
            phasename: requirement analysis
            phasetarget: "produce requirements doc"
            llm-model: claude-sonnet-4.6
          - role: architect
            phasename: system design
            phasetarget: "produce design doc"
            llm-model: ""
        workflowB:
          - role: coder
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
    for wf_name, phase_list in raw.items():
        if not isinstance(phase_list, list):
            logger.warning("Workflow '%s' is not a list, skipping", wf_name)
            continue

        phases: list[Phase] = []
        for item in phase_list:
            if not isinstance(item, dict):
                continue
            phases.append(Phase(
                role=item.get("role", ""),
                phasename=item.get("phasename", ""),
                phasetarget=item.get("phasetarget", ""),
                llm_model=item.get("llm-model", ""),
                extra_flags=item.get("extra-flags", ""),
            ))
        workflows[wf_name] = Workflow(name=wf_name, phases=phases)
        logger.info("Loaded workflow '%s' with %d phases", wf_name, len(phases))

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
