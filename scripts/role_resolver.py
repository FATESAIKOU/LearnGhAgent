"""Role resolver — determine agent role from issue labels."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

ROLE_LABEL_PREFIX = "role:"


def resolve_role(labels: list[dict[str, Any]], default_role: str) -> str:
    """Determine role from issue labels. Returns default_role if none found."""
    for label in labels:
        name = label.get("name", "")
        if name.startswith(ROLE_LABEL_PREFIX):
            role = name[len(ROLE_LABEL_PREFIX):]
            if role:
                logger.debug("Resolved role '%s' from label '%s'", role, name)
                return role

    logger.debug("No role label found, using default: '%s'", default_role)
    return default_role
