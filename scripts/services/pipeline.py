"""Pipeline service — orchestrates the issue processing workflow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from domain.workflow import Workflow
from ports.agent_port import AgentPort
from ports.git_port import GitPort
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
        git_port: GitPort,
        agent_port: AgentPort,
        hooks_port: HooksPort,
        role_service: RoleService,
        workflow_service: WorkflowService,
        prompt_service: PromptService,
    ):
        self.github = github_port
        self.git = git_port
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

        if not resolved.role:
            logger.debug("Issue #%d: no matching role label, skipping", number)
            return

        logger.info(
            "Issue #%d: processing (role=%s, workflow=%s, phase=%s)",
            number, resolved.role, resolved.workflow_name or "none",
            resolved.phase_name or "none",
        )

        # Step 2: Resolve workflow/phase
        current_workflow = None
        current_phase_idx = None
        phase = None

        if resolved.workflow_name and resolved.workflow_name in workflows:
            current_workflow = workflows[resolved.workflow_name]
            current_phase_idx, phase = self.workflow_service.resolve_phase(
                current_workflow, resolved.phase_name,
                config.target_issue_repo, number,
            )
            if current_phase_idx is not None:
                logger.info(
                    "Issue #%d: workflow '%s' phase '%s' (idx=%d)",
                    number, resolved.workflow_name,
                    current_workflow.phases[current_phase_idx].phasename,
                    current_phase_idx,
                )

        # Step 3: Init workspace — clone repos & create branches
        repos = current_workflow.repos if current_workflow else []
        if repos:
            try:
                self.git.init_workspace(repos, number)
            except Exception as e:
                logger.error("Issue #%d: workspace init failed: %s", number, e)
                return

        # Step 4: Build prompt
        try:
            prompt = self.prompt_service.build_prompt(
                config.target_issue_repo, number, resolved.role,
                config.agents_dir, phase, repos,
            )
        except Exception as e:
            logger.error("Issue #%d: failed to build prompt: %s", number, e)
            return

        # Step 5: Run workspace-init hooks (e.g. ban-git-write)
        ws_init_scripts = phase.workspace_init if phase else []
        if ws_init_scripts:
            logger.info(
                "Issue #%d: running workspace-init scripts: %s",
                number, ws_init_scripts,
            )
            self.hooks.run_workspace_scripts(ws_init_scripts)

        # Step 6: Run agent (model priority: workflow phase > env default)
        effective_model = (phase.llm_model if phase else "") or config.copilot_model
        extra_flags = phase.extra_flags if phase else ""
        result = self.agent.run(
            prompt=prompt,
            role=resolved.role,
            agents_dir=config.agents_dir,
            timeout=config.agent_timeout,
            model=effective_model,
            extra_flags=extra_flags,
        )

        # Step 7: Run workspace-cleanup hooks (always after ws-init)
        if ws_init_scripts:
            ws_cleanup_scripts = phase.workspace_cleanup if phase else []
            if ws_cleanup_scripts:
                logger.info(
                    "Issue #%d: running workspace-cleanup scripts: %s",
                    number, ws_cleanup_scripts,
                )
                self.hooks.run_workspace_scripts(ws_cleanup_scripts)

        # Step 8: Push workspace changes (even on timeout/failure for partial work)
        if repos:
            self._try_push(repos, number, config.target_issue_repo, resolved.phase_name)

        # Step 9: Check result — stop on timeout or failure
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

        # Step 10: Post comment
        phase_info = ""
        if resolved.phase_name:
            phase_info = f" | phase: {resolved.phase_name}"
        if result.output:
            comment_body = (
                f"## Agent Report (role: {resolved.role}{phase_info})\n\n{result.output}"
            )
            try:
                self.github.post_comment(config.target_issue_repo, number, comment_body)
            except Exception as e:
                logger.error("Issue #%d: failed to post comment: %s", number, e)
                return

        # Step 11: Workflow transition
        if current_workflow and current_phase_idx is not None:
            try:
                self.workflow_service.advance_phase(
                    current_workflow, current_phase_idx, resolved,
                    config.target_issue_repo, number,
                )
            except Exception as e:
                logger.error("Issue #%d: failed to advance workflow: %s", number, e)

        elif resolved.role_label:
            # No workflow — just remove the role label after processing
            try:
                self.github.remove_label(
                    config.target_issue_repo, number, resolved.role_label,
                )
            except Exception as e:
                logger.warning(
                    "Issue #%d: failed to remove label '%s': %s",
                    number, resolved.role_label, e,
                )

    def _try_push(
        self,
        repos: list,
        number: int,
        issue_repo: str,
        phase_name: str = "",
    ) -> None:
        """Push workspace changes, logging but not raising on failure."""
        try:
            self.git.push_workspace(repos, number, issue_repo, phase_name)
        except Exception as e:
            logger.error("Issue #%d: push_workspace failed: %s", number, e)
