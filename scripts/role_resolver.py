"""Role resolver — determine agent role from issue labels.

New logic:
  1. Extract all `role:xxx` labels from an issue.
  2. For each, check that `agents/xxx/` directory exists.
  3. If ENABLED_AGENTS is set, only accept roles in that list.
  4. Also extract `workflow:xxx` label if present.
  5. Returns (roles, workflow_name) — roles may have multiple if labels exist,
     but typically only one is active at a time.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

ROLE_LABEL_PREFIX = "role:"
WORKFLOW_LABEL_PREFIX = "workflow:"


@dataclass
class ResolvedLabels:
    """Result of label resolution."""
    role: str  # Active role (empty if none matched)
    role_label: str  # The full label string e.g. "role:manager"
    workflow_name: str  # Extracted from "workflow:xxx" label (empty if none)
    phase_name: str  # Extracted from "phase:xxx" label (empty if none)


def resolve_labels(
    labels: list[dict[str, Any]],
    agents_dir: str,
    enabled_agents: list[str],
) -> ResolvedLabels:
    """Determine role, workflow, and phase from issue labels.

    Args:
        labels: List of label dicts from GitHub API.
        agents_dir: Path to agents directory to validate role existence.
        enabled_agents: List of enabled agent names. Empty = all enabled.

    Returns:
        ResolvedLabels with matched role, workflow, and phase.
    """
    role = ""
    role_label = ""
    workflow_name = ""
    phase_name = ""

    for label in labels:
        name = label.get("name", "")

        # Extract role
        if name.startswith(ROLE_LABEL_PREFIX) and not role:
            candidate = name[len(ROLE_LABEL_PREFIX):]
            if not candidate:
                continue

            # Check agent directory exists
            agent_path = os.path.join(agents_dir, candidate)
            if not os.path.isdir(agent_path):
                logger.warning("Role '%s' has no matching agent dir at %s, skipping", candidate, agent_path)
                continue

            # Check enabled list
            if enabled_agents and candidate not in enabled_agents:
                logger.info("Role '%s' is not in ENABLED_AGENTS, skipping", candidate)
                continue

            role = candidate
            role_label = name
            logger.debug("Resolved role '%s' from label '%s'", role, name)

        # Extract workflow
        elif name.startswith(WORKFLOW_LABEL_PREFIX) and not workflow_name:
            workflow_name = name[len(WORKFLOW_LABEL_PREFIX):]
            logger.debug("Resolved workflow '%s' from label '%s'", workflow_name, name)

        # Extract phase
        elif name.startswith("phase:") and not phase_name:
            phase_name = name[len("phase:"):]
            logger.debug("Resolved phase '%s' from label '%s'", phase_name, name)

    if not role:
        logger.debug("No valid role label found")

    return ResolvedLabels(
        role=role,
        role_label=role_label,
        workflow_name=workflow_name,
        phase_name=phase_name,
    )

