"""Role service — determines agent role from issue labels."""

import logging
import os
from typing import Any

from domain.models import ResolvedLabels

logger = logging.getLogger(__name__)

ROLE_LABEL_PREFIX = "role:"
WORKFLOW_LABEL_PREFIX = "workflow:"
PHASE_LABEL_PREFIX = "phase:"


class RoleService:
    """Resolves agent role, workflow, and phase from issue labels."""

    def resolve_labels(
        self,
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
                    logger.warning(
                        "Role '%s' has no matching agent dir at %s, skipping",
                        candidate, agent_path,
                    )
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
            elif name.startswith(PHASE_LABEL_PREFIX) and not phase_name:
                phase_name = name[len(PHASE_LABEL_PREFIX):]
                logger.debug("Resolved phase '%s' from label '%s'", phase_name, name)

        return ResolvedLabels(
            role=role,
            role_label=role_label,
            workflow_name=workflow_name,
            phase_name=phase_name,
        )
