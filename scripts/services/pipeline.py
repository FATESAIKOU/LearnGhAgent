"""Pipeline service — orchestrates the issue processing workflow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from domain.workflow import Workflow
from ports.agent_port import AgentPort
from ports.github_port import GitHubPort
from ports.hooks_port import HooksPort
from services.role_service import RoleService
from services.workflow_service import WorkflowService
from services.prompt_service import PromptService

if TYPE_CHECKING:
    from config import Config

logger = logging.getLogger(__name__)


class PipelineService:
    """Main use-case: process a single GitHub issue through the full pipeline."""

    def __init__(
        self,
        github_port: GitHubPort,
        agent_port: AgentPort,
        hooks_port: HooksPort,
        role_service: RoleService,
        workflow_service: WorkflowService,
        prompt_service: PromptService,
    ):
        self.github = github_port
        self.agent = agent_port
        self.hooks = hooks_port
        self.role_service = role_service
        self.workflow_service = workflow_service
        self.prompt_service = prompt_service

    def process_issue(
        self,
        number: int,
        labels: list[dict],
        config: "Config",
        workflows: dict[str, Workflow],
    ) -> None:
        """Process a single issue: check labels, run agent, advance workflow."""

        # Step 1: Resolve labels
        resolved = self.role_service.resolve_labels(
            labels, config.agents_dir, config.enabled_agents,
        )

        # Trigger requires workflow:xxx label
        if not resolved.workflow_name:
            logger.debug("Issue #%d: no workflow label, skipping", number)
            return

        # Skip completed workflows (phase:end)
        if resolved.phase_name == "end":
            logger.debug("Issue #%d: workflow already completed (phase:end), skipping", number)
            return

        # Step 2: Resolve workflow/phase
        current_workflow = workflows.get(resolved.workflow_name)
        if not current_workflow:
            logger.warning(
                "Issue #%d: workflow '%s' not found in loaded workflows, skipping",
                number, resolved.workflow_name,
            )
            return

        current_phase_idx, phase = self.workflow_service.resolve_phase(
            current_workflow, resolved.phase_name,
            config.target_issue_repo, number,
        )

        if phase is None:
            logger.warning("Issue #%d: could not resolve phase, skipping", number)
            return

        # Role comes from workflow phase definition
        effective_role = phase.role
        logger.info(
            "Issue #%d: processing (role=%s, workflow=%s, phase=%s)",
            number, effective_role, resolved.workflow_name,
            phase.phasename,
        )

        # Step 3: Build phase_env for hook scripts
        phase_env = self.workflow_service.build_phase_env(
            current_workflow, phase, number, config.target_issue_repo,
        )

        # Step 4: Run workspace-init hooks (e.g. clone-and-branch, ban-git-write)
        ws_init_scripts = phase.workspace_init
        if ws_init_scripts:
            logger.info(
                "Issue #%d: running workspace-init scripts: %s",
                number, ws_init_scripts,
            )
            init_ok = self.hooks.run_workspace_scripts(ws_init_scripts, phase_env)
            if not init_ok:
                logger.error("Issue #%d: workspace-init failed, skipping", number)
                return

        # Step 5: Build prompt
        try:
            prompt = self.prompt_service.build_prompt(
                config.target_issue_repo, number, effective_role,
                config.agents_dir, phase, current_workflow.repos,
            )
        except Exception as e:
            logger.error("Issue #%d: failed to build prompt: %s", number, e)
            return

        # Step 6: Run agent (model priority: workflow phase > env default)
        effective_model = phase.llm_model or config.copilot_model
        result = self.agent.run(
            prompt=prompt,
            role=effective_role,
            agents_dir=config.agents_dir,
            timeout=config.agent_timeout,
            model=effective_model,
        )

        # Step 7: Run workspace-cleanup hooks (always after ws-init)
        if ws_init_scripts:
            ws_cleanup_scripts = phase.workspace_cleanup
            if ws_cleanup_scripts:
                logger.info(
                    "Issue #%d: running workspace-cleanup scripts: %s",
                    number, ws_cleanup_scripts,
                )
                self.hooks.run_workspace_scripts(ws_cleanup_scripts, phase_env)

        # Step 8: Check result — stop on timeout or failure
        if result.timed_out:
            logger.warning(
                "Issue #%d: agent timed out after %ds", number, config.agent_timeout,
            )
            return

        if result.exit_code != 0:
            logger.error(
                "Issue #%d: agent failed with exit code %d", number, result.exit_code,
            )
            return

        # Step 9: Post comment
        phase_info = f" | phase: {phase.phasename}"
        if result.output:
            comment_body = (
                f"## Agent Report (role: {effective_role}{phase_info})\n\n{result.output}"
            )
            try:
                self.github.post_comment(config.target_issue_repo, number, comment_body)
            except Exception as e:
                logger.error("Issue #%d: failed to post comment: %s", number, e)
                return

        # Step 10: Workflow transition
        try:
            self.workflow_service.advance_phase(
                current_workflow, current_phase_idx,
                config.target_issue_repo, number,
            )
        except Exception as e:
            logger.error("Issue #%d: failed to advance workflow: %s", number, e)
