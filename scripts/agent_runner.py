"""Agent runner — execute gh copilot as a subprocess."""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    exit_code: int
    output: str
    timed_out: bool


def run_agent(
    prompt: str,
    role: str,
    agents_dir: str,
    timeout: int,
    copilot_model: str = "",
) -> AgentResult:
    """Run gh copilot with the given prompt and return the result."""

    # Read role config
    config_path = os.path.join(agents_dir, role, "config.json")
    model = ""
    extra_flags = ""
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            model = config.get("model", "")
            extra_flags = config.get("extra_flags", "")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read role config %s: %s", config_path, e)

    # Build command
    cmd = [
        "gh", "copilot",
        "-p", prompt,
        "--yolo",
        "-s",
        "--no-ask-user",
        "--add-dir", "/workspace",
    ]

    # Model selection: role config > env var
    effective_model = model or copilot_model
    if effective_model:
        cmd.extend(["--model", effective_model])

    # Extra flags
    if extra_flags:
        cmd.extend(extra_flags.split())

    logger.info("Running agent with role '%s' (timeout=%ds)", role, timeout)
    logger.debug("Command: %s", " ".join(cmd[:6]) + " ...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return AgentResult(
            exit_code=result.returncode,
            output=result.stdout.strip(),
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Agent timed out after %ds", timeout)
        return AgentResult(
            exit_code=-1,
            output="",
            timed_out=True,
        )
