#!/usr/bin/env python3
"""Main entry point — Composition Root + Polling Loop (Inbound Adapter).

Assembles all dependencies (Adapters → Services) and runs the main polling loop.
"""

import logging
import sys
import time

from config import load_config

from adapters.github_adapter import GhCliGitHubAdapter
from adapters.agent_adapter import CopilotCliAgentAdapter
from adapters.hooks_adapter import SubprocessHooksAdapter

from services.role_service import RoleService
from services.workflow_service import WorkflowService
from services.prompt_service import PromptService
from services.pipeline import PipelineService


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
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()

    # --- Build Adapters (Outbound) ---
    github_adapter = GhCliGitHubAdapter()
    agent_adapter = CopilotCliAgentAdapter()
    hooks_adapter = SubprocessHooksAdapter()

    # --- Build Services (inject Ports/Adapters) ---
    role_service = RoleService()
    workflow_service = WorkflowService(github_port=github_adapter)
    prompt_service = PromptService(github_port=github_adapter)
    pipeline = PipelineService(
        github_port=github_adapter,
        agent_port=agent_adapter,
        hooks_port=hooks_adapter,
        role_service=role_service,
        workflow_service=workflow_service,
        prompt_service=prompt_service,
    )

    # --- Load Workflows ---
    workflows = workflow_service.load_workflows(config.workflow_file)

    # --- Startup logging ---
    logger.info("Agent loop started for %s", config.target_issue_repo)
    logger.info("Poll interval: %ds, Timeout: %ds", config.poll_interval, config.agent_timeout)
    if config.enabled_agents:
        logger.info("Enabled agents: %s", ", ".join(config.enabled_agents))
    else:
        logger.info("All agents enabled")
    if workflows:
        logger.info("Loaded workflows: %s", ", ".join(workflows.keys()))

    # --- Polling Loop ---
    while True:
        logger.info("Polling issues for %s...", config.target_issue_repo)

        try:
            issues = github_adapter.list_open_issues(config.target_issue_repo)
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
                pipeline.process_issue(number, labels, config, workflows)
            except Exception as e:
                logger.error("Issue #%d: unexpected error: %s", number, e)

        logger.info("Sleeping %ds...", config.poll_interval)
        time.sleep(config.poll_interval)


if __name__ == "__main__":
    main()
