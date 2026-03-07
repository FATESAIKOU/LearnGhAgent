"""Agent runner — execute gh copilot as a subprocess with real-time output."""

import json
import logging
import os
import subprocess
import threading
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
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
            bufsize=1,  # line-buffered
        )

        # Watchdog timer — kill process on timeout
        timed_out_flag = threading.Event()

        def _watchdog():
            timed_out_flag.set()
            proc.kill()

        timer = threading.Timer(timeout, _watchdog)
        timer.start()

        # Stream output line by line
        lines: list[str] = []
        try:
            for line in proc.stdout:            # type: ignore[union-attr]
                stripped = line.rstrip("\n")
                logger.info("[copilot] %s", stripped)
                lines.append(line)
        finally:
            proc.wait()
            timer.cancel()

        if timed_out_flag.is_set():
            logger.warning("Agent timed out after %ds", timeout)
            return AgentResult(
                exit_code=-1,
                output="".join(lines).strip(),
                timed_out=True,
            )

        return AgentResult(
            exit_code=proc.returncode,
            output="".join(lines).strip(),
            timed_out=False,
        )
    except Exception as e:
        logger.error("Agent execution error: %s", e)
        return AgentResult(
            exit_code=-1,
            output="",
            timed_out=False,
        )
