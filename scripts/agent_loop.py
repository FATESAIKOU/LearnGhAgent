#!/usr/bin/env python3
"""Main agent loop — polls GitHub issues and dispatches agents with workflow support."""

import logging
import sys
import time
from datetime import datetime, timezone

from config import Config, load_config
from github_client import (
    add_label,
    get_issue,
    get_issue_comments,
    get_latest_activity_time,
    list_open_issues,
    post_comment,
    remove_label,
)
from state_manager import StateManager
from role_resolver import resolve_labels
from prompt_builder import build_prompt
from agent_runner import run_agent
from workflow_loader import (
    Workflow,
    find_phase_by_label,
    get_next_phase,
    load_workflows,
)

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
    workflows: dict[str, Workflow],
) -> None:
    """Process a single issue: check labels, run agent, advance workflow."""

    # Step 1: Resolve labels
    resolved = resolve_labels(labels, config.agents_dir, config.enabled_agents)

    if not resolved.role:
        logger.debug("Issue #%d: no matching role label, skipping", number)
        return

    # Step 2: Get latest activity time
    try:
        latest_time = get_latest_activity_time(config.owner, config.repo, number)
    except Exception as e:
        logger.error("Issue #%d: failed to get activity time: %s", number, e)
        return

    # Step 3: Compare with state
    last_processed = state.get_last_processed(number)
    if last_processed and last_processed >= latest_time:
        logger.debug("Issue #%d: no new activity, skipping", number)
        return

    logger.info("Issue #%d: new activity detected (role=%s, workflow=%s, phase=%s)",
                number, resolved.role, resolved.workflow_name or "none",
                resolved.phase_name or "none")

    # Step 4: Determine model & flags — workflow phase > env default
    phase_model = ""
    phase_extra_flags = ""
    current_workflow = None
    current_phase_idx = None
    if resolved.workflow_name and resolved.workflow_name in workflows:
        current_workflow = workflows[resolved.workflow_name]
        if resolved.phase_name:
            current_phase_idx = find_phase_by_label(current_workflow, resolved.phase_name)
            if current_phase_idx is None:
                logger.warning("Issue #%d: phase '%s' not found in workflow '%s', "
                               "falling back to first phase",
                               number, resolved.phase_name, resolved.workflow_name)

        # If no phase label or phase not found, default to first phase
        if current_phase_idx is None and current_workflow.phases:
            current_phase_idx = 0
            first_phase = current_workflow.phases[0]
            logger.info("Issue #%d: defaulting to first phase '%s' of workflow '%s'",
                        number, first_phase.phasename, resolved.workflow_name)
            # Auto-add the phase label for tracking
            try:
                add_label(config.target_repo, number, f"phase:{first_phase.phasename}")
            except Exception as e:
                logger.warning("Issue #%d: failed to auto-add phase label: %s", number, e)

        if current_phase_idx is not None:
            phase_model = current_workflow.phases[current_phase_idx].llm_model
            phase_extra_flags = current_workflow.phases[current_phase_idx].extra_flags
            logger.info("Issue #%d: workflow '%s' phase '%s' (idx=%d)",
                        number, resolved.workflow_name,
                        current_workflow.phases[current_phase_idx].phasename,
                        current_phase_idx)

    # Step 5: Fetch issue data and build prompt (include phase target in prompt)
    try:
        issue = get_issue(config.owner, config.repo, number)
        comments = get_issue_comments(config.owner, config.repo, number)

        # Build extra context from workflow phase
        phase_context = ""
        if current_workflow and current_phase_idx is not None:
            phase = current_workflow.phases[current_phase_idx]
            phase_context = (
                f"\n\n## Current Workflow Phase\n"
                f"- **Workflow:** {current_workflow.name}\n"
                f"- **Phase:** {phase.phasename}\n"
                f"- **Target:** {phase.phasetarget}\n"
            )

        prompt = build_prompt(issue, comments, resolved.role, config.agents_dir,
                              extra_context=phase_context)
    except Exception as e:
        logger.error("Issue #%d: failed to build prompt: %s", number, e)
        return

    # Step 6: Run agent (model priority: workflow phase > env default)
    effective_model = phase_model or config.copilot_model
    result = run_agent(
        prompt=prompt,
        role=resolved.role,
        agents_dir=config.agents_dir,
        timeout=config.agent_timeout,
        copilot_model=effective_model,
        extra_flags=phase_extra_flags,
    )

    if result.timed_out:
        logger.warning("Issue #%d: agent timed out after %ds", number, config.agent_timeout)
        return

    if result.exit_code != 0:
        logger.error("Issue #%d: agent failed with exit code %d", number, result.exit_code)
        return

    # Step 7: Post comment
    phase_info = ""
    if resolved.phase_name:
        phase_info = f" | phase: {resolved.phase_name}"
    if result.output:
        comment_body = f"## Agent Report (role: {resolved.role}{phase_info})\n\n{result.output}"
        try:
            post_comment(config.target_repo, number, comment_body)
        except Exception as e:
            logger.error("Issue #%d: failed to post comment: %s", number, e)
            return

    # Step 8: Workflow transition — remove current labels, add next phase labels
    has_next_phase = False
    if current_workflow and current_phase_idx is not None:
        try:
            has_next_phase = _advance_workflow(config, number, resolved, current_workflow, current_phase_idx)
        except Exception as e:
            logger.error("Issue #%d: failed to advance workflow: %s", number, e)

    elif resolved.role_label:
        # No workflow — just remove the role label after processing
        try:
            remove_label(config.target_repo, number, resolved.role_label)
        except Exception as e:
            logger.warning("Issue #%d: failed to remove label '%s': %s",
                           number, resolved.role_label, e)

    # Step 9: Update state
    # If there's a next phase, reset state so the next poll picks it up immediately
    if has_next_phase:
        try:
            state.clear_last_processed(number)
            logger.info("Issue #%d: state cleared for next phase", number)
        except Exception as e:
            logger.error("Issue #%d: failed to clear state: %s", number, e)
    else:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            state.update_last_processed(number, now)
        except Exception as e:
            logger.error("Issue #%d: failed to update state: %s", number, e)


def _advance_workflow(
    config: Config,
    number: int,
    resolved,
    workflow: Workflow,
    current_phase_idx: int,
) -> bool:
    """Remove current phase labels, add next phase labels.

    Returns True if there is a next phase, False if workflow is complete.
    """
    repo = config.target_repo

    # Use the actual current phase name from the workflow (not just resolved.phase_name,
    # which may be empty if the phase was auto-inferred from workflow's first phase)
    current_phase = workflow.phases[current_phase_idx]

    # Remove current role + phase labels
    if resolved.role_label:
        remove_label(repo, number, resolved.role_label)
    # Always remove the current phase label (whether it came from the issue or was auto-added)
    try:
        remove_label(repo, number, f"phase:{current_phase.phasename}")
    except Exception:
        pass  # Label might not exist if phase was auto-inferred and add_label failed

    # Get next phase
    next_phase = get_next_phase(workflow, current_phase_idx)
    if next_phase:
        # Add next role + phase labels
        add_label(repo, number, f"role:{next_phase.role}")
        add_label(repo, number, f"phase:{next_phase.phasename}")
        logger.info("Issue #%d: advanced to next phase -> role:%s phase:%s",
                     number, next_phase.role, next_phase.phasename)
        return True
    else:
        logger.info("Issue #%d: workflow '%s' completed (no more phases)",
                     number, workflow.name)
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()
    state = StateManager(config.state_file)
    workflows = load_workflows(config.workflow_file)

    logger.info("Agent loop started for %s", config.target_repo)
    logger.info("Poll interval: %ds, Timeout: %ds", config.poll_interval, config.agent_timeout)
    if config.enabled_agents:
        logger.info("Enabled agents: %s", ", ".join(config.enabled_agents))
    else:
        logger.info("All agents enabled")
    if workflows:
        logger.info("Loaded workflows: %s", ", ".join(workflows.keys()))

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
                process_issue(number, labels, config, state, workflows)
            except Exception as e:
                logger.error("Issue #%d: unexpected error: %s", number, e)

        logger.info("Sleeping %ds...", config.poll_interval)
        time.sleep(config.poll_interval)


if __name__ == "__main__":
    main()
