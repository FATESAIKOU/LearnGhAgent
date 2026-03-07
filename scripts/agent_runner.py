"""Agent runner — execute gh copilot as a subprocess with real-time JSON output."""

import json
import logging
import os
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    exit_code: int
    output: str
    timed_out: bool


def _process_jsonl_line(raw: str, state: dict) -> None:
    """Parse one JSONL line from copilot and log it in a human-readable way.

    Also accumulates the final assistant message into state["final_message"].
    """
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # Not JSON — print raw (e.g. copilot startup messages)
        logger.info("[copilot] %s", raw.rstrip())
        return

    event_type = obj.get("type", "")
    data = obj.get("data", {})

    # --- Thinking / reasoning ---
    if event_type == "assistant.reasoning_delta":
        chunk = data.get("deltaContent", "")
        state.setdefault("reasoning_buf", "")
        state["reasoning_buf"] += chunk
        return  # accumulate, print on reasoning complete

    if event_type == "assistant.reasoning":
        content = data.get("content", state.get("reasoning_buf", ""))
        if content:
            logger.info("[thinking] %s", content)
        state["reasoning_buf"] = ""
        return

    # --- Tool calls ---
    if event_type == "tool.execution_start":
        tool_name = data.get("toolName", "?")
        args = data.get("arguments", {})
        desc = args.get("description", args.get("command", args.get("query", "")))
        if desc:
            logger.info("[tool:start] %s — %s", tool_name, desc[:200])
        else:
            logger.info("[tool:start] %s %s", tool_name, json.dumps(args, ensure_ascii=False)[:200])
        return

    if event_type == "tool.execution_complete":
        tool_name = data.get("toolName", "?")
        success = data.get("success", None)
        result = data.get("result", {})
        content = result.get("content", "")
        # Truncate long tool output for readability
        preview = content[:300].replace("\n", "\\n") if content else ""
        logger.info("[tool:done] %s success=%s %s", tool_name, success, preview)
        return

    # --- Streaming message deltas ---
    if event_type == "assistant.message_delta":
        chunk = data.get("deltaContent", "")
        state.setdefault("message_buf", "")
        state["message_buf"] += chunk
        return  # accumulate, print on message complete

    # --- Final message ---
    if event_type == "assistant.message":
        content = data.get("content", "")
        if content:
            state["final_message"] = content
            logger.info("[response] %s", content[:500])
        elif state.get("message_buf"):
            state["final_message"] = state["message_buf"]
            logger.info("[response] %s", state["message_buf"][:500])
        state["message_buf"] = ""

        tool_requests = data.get("toolRequests", [])
        if tool_requests:
            names = [tr.get("name", "?") for tr in tool_requests]
            logger.info("[tool:call] requesting: %s", ", ".join(names))
        return

    # --- Stats / result ---
    if event_type == "result":
        usage = data.get("usage", {})
        if usage:
            premium = usage.get("premiumRequests", "?")
            api_ms = usage.get("totalApiDurationMs", "?")
            session_ms = usage.get("sessionDurationMs", "?")
            logger.info("[stats] premium_requests=%s api_time=%sms session_time=%sms", premium, api_ms, session_ms)
        return

    # --- Other events — log type for debugging ---
    if event_type not in ("user.message", "assistant.turn_start", "assistant.turn_end",
                          "assistant.message_delta", "assistant.reasoning_delta"):
        logger.debug("[event] %s", event_type)


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
        "--output-format", "json",
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
            cwd="/workspace",
        )

        # Watchdog timer — kill process on timeout
        timed_out_flag = threading.Event()

        def _watchdog():
            timed_out_flag.set()
            proc.kill()

        timer = threading.Timer(timeout, _watchdog)
        timer.start()

        # Stream JSONL output line by line with structured parsing
        state: dict = {"final_message": "", "reasoning_buf": "", "message_buf": ""}
        raw_lines: list[str] = []
        try:
            for line in proc.stdout:            # type: ignore[union-attr]
                raw_lines.append(line)
                stripped = line.strip()
                if stripped:
                    _process_jsonl_line(stripped, state)
        finally:
            proc.wait()
            timer.cancel()

        # Extract the final response text for posting as comment
        final_output = state.get("final_message", "")

        if timed_out_flag.is_set():
            logger.warning("Agent timed out after %ds", timeout)
            return AgentResult(
                exit_code=-1,
                output=final_output,
                timed_out=True,
            )

        return AgentResult(
            exit_code=proc.returncode,
            output=final_output,
            timed_out=False,
        )
    except Exception as e:
        logger.error("Agent execution error: %s", e)
        return AgentResult(
            exit_code=-1,
            output="",
            timed_out=False,
        )
