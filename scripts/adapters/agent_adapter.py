"""Agent adapter — implements AgentPort using gh copilot CLI."""

import logging
import subprocess
import threading

from domain.models import AgentResult

logger = logging.getLogger(__name__)


class CopilotCliAgentAdapter:
    """Implements AgentPort via the gh copilot CLI."""

    def run(
        self,
        prompt: str,
        role: str,
        agents_dir: str,
        timeout: int,
        model: str = "",
        extra_flags: str = "",
    ) -> AgentResult:
        """Run gh copilot with the given prompt and return the result."""

        # Build command
        cmd = [
            "gh", "copilot",
            "-p", prompt,
            "--yolo",
            "--no-ask-user",
            "--add-dir", "/workspace",
        ]

        # Model selection
        if model:
            cmd.extend(["--model", model])

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
                for line in proc.stdout:  # type: ignore[union-attr]
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
