"""Prompt builder — assemble the full prompt for gh copilot."""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_INSTRUCTIONS = (
    "You are an AI assistant. Execute the task described in the issue."
)


def build_prompt(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    role: str,
    agents_dir: str,
) -> str:
    """Build the full prompt from issue data, comments, and role instructions."""

    # Load role instructions
    instructions_path = os.path.join(agents_dir, role, "instructions.md")
    if os.path.isfile(instructions_path):
        with open(instructions_path, "r") as f:
            instructions = f.read().strip()
        logger.debug("Loaded instructions from %s", instructions_path)
    else:
        instructions = DEFAULT_INSTRUCTIONS
        logger.debug("Using default instructions (no file at %s)", instructions_path)

    # Extract issue fields
    number = issue.get("number", "?")
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    author = issue.get("user", {}).get("login", "unknown")

    # Format comments
    comment_lines = []
    for c in comments:
        user = c.get("user", {}).get("login", "unknown")
        time = c.get("created_at", "")
        cbody = c.get("body", "")
        comment_lines.append(f"[{user} at {time}]:\n{cbody}")
    comments_text = "\n\n".join(comment_lines) if comment_lines else "(no comments)"

    # Assemble
    prompt = f"""{instructions}

---

# Issue #{number}: {title}

**Author:** {author}

## Description
{body}

## Comments
{comments_text}

---

Please execute the task and provide a summary of what you did."""

    return prompt
