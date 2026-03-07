#!/usr/bin/env python3
"""Main agent loop — polls GitHub issues and dispatches agents."""

import logging
import sys
import time
from datetime import datetime, timezone

from config import Config, load_config
from github_client import (
    get_issue,
    get_issue_comments,
    get_latest_activity_time,
    list_open_issues,
    post_comment,
)
from state_manager import StateManager
from role_resolver import resolve_role
from prompt_builder import build_prompt
from agent_runner import run_agent

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
)
logging.Formatter.converter = time.gmtime  # UTC timestamps
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Issue processing
# ---------------------------------------------------------------------------

def process_issue(
    number: int,
    labels: list[dict],
    config: Config,
    state: StateManager,
) -> None:
    """Process a single issue: check activity, run agent, post result."""

    # Step 1: Get latest activity time
    try:
        latest_time = get_latest_activity_time(config.owner, config.repo, number)
    except Exception as e:
        logger.error("Issue #%d: failed to get activity time: %s", number, e)
        return

    # Step 2: Compare with state
    last_processed = state.get_last_processed(number)
    if last_processed and last_processed >= latest_time:
        logger.debug("Issue #%d: no new activity, skipping", number)
        return

    logger.info("Issue #%d: new activity detected", number)

    # Step 3: Determine role
    role = resolve_role(labels, config.default_role)

    # Step 4: Fetch issue data and build prompt
    try:
        issue = get_issue(config.owner, config.repo, number)
        comments = get_issue_comments(config.owner, config.repo, number)
        prompt = build_prompt(issue, comments, role, config.agents_dir)
    except Exception as e:
        logger.error("Issue #%d: failed to build prompt: %s", number, e)
        return

    # Step 5: Run agent
    result = run_agent(
        prompt=prompt,
        role=role,
        agents_dir=config.agents_dir,
        timeout=config.agent_timeout,
        copilot_model=config.copilot_model,
    )

    if result.timed_out:
        logger.warning("Issue #%d: agent timed out after %ds", number, config.agent_timeout)
        return

    if result.exit_code != 0:
        logger.error("Issue #%d: agent failed with exit code %d", number, result.exit_code)
        return

    # Step 6: Post comment
    if result.output:
        comment_body = f"## Agent Report (role: {role})\n\n{result.output}"
        try:
            post_comment(config.target_repo, number, comment_body)
        except Exception as e:
            logger.error("Issue #%d: failed to post comment: %s", number, e)
            return

    # Step 7: Update state
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        state.update_last_processed(number, now)
    except Exception as e:
        logger.error("Issue #%d: failed to update state: %s", number, e)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()
    state = StateManager(config.state_file)

    logger.info("Agent loop started for %s", config.target_repo)
    logger.info("Poll interval: %ds, Timeout: %ds", config.poll_interval, config.agent_timeout)

    while True:
        logger.info("Polling issues for %s...", config.target_repo)

        try:
            issues = list_open_issues(config.target_repo)
        except Exception as e:
            logger.error("Failed to list issues: %s", e)
            issues = []

        logger.info("Found %d open issues", len(issues))

        for issue_item in issues:
            number = issue_item.get("number")
            labels = issue_item.get("labels", [])

            if number is None:
                continue

            try:
                process_issue(number, labels, config, state)
            except Exception as e:
                logger.error("Issue #%d: unexpected error: %s", number, e)

        logger.info("Sleeping %ds...", config.poll_interval)
        time.sleep(config.poll_interval)


if __name__ == "__main__":
    main()
