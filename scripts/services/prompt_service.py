"""Prompt service — assembles the full prompt for the AI agent."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from ports.github_port import GitHubPort

if TYPE_CHECKING:
    from domain.workflow import Phase, RepoConfig

logger = logging.getLogger(__name__)

DEFAULT_INSTRUCTIONS = (
    "You are an AI assistant. Execute the task described in the issue."
)


class PromptService:
    """Builds the complete prompt from issue data, role instructions, and workflow context."""

    def __init__(self, github_port: GitHubPort):
        self.github = github_port

    def build_prompt(
        self,
        repo: str,
        issue_number: int,
        role: str,
        agents_dir: str,
        phase: "Phase | None",
        workflow_repos: list["RepoConfig"],
    ) -> str:
        """Build the full prompt for the agent.

        Args:
            repo: Issue repo in 'owner/repo' format.
            issue_number: Issue number to process.
            role: Agent role name.
            agents_dir: Path to agents directory.
            phase: Current workflow phase (or None).
            workflow_repos: List of repos from the workflow config.

        Returns:
            Complete prompt string.
        """
        # 1. Fetch issue data
        issue = self.github.get_issue(repo, issue_number)
        comments = self.github.get_issue_comments(repo, issue_number)

        # 2. Build extra context
        extra_context = self._build_extra_context(phase, workflow_repos, issue_number)

        # 3. Assemble prompt
        return self._assemble_prompt(issue, comments, role, agents_dir, extra_context)

    def _build_extra_context(
        self,
        phase: "Phase | None",
        repos: list["RepoConfig"],
        issue_number: int,
    ) -> str:
        """Build extra context from workflow phase and repos info."""
        context = ""

        # Phase context
        if phase:
            context += f"\n\n## Current Workflow Phase\n- **Phase:** {phase.phasename}\n"
            if phase.phase_prompt:
                branch = f"agent/issue-{issue_number}"
                rendered = phase.phase_prompt
                rendered = rendered.replace("{BRANCH_NAME}", branch)
                rendered = rendered.replace("{ISSUE_NUMBER}", str(issue_number))
                context += f"\n{rendered}\n"

        # Repos context
        if repos:
            context += "\n\n## Available Repositories\n"
            context += (
                "The following repos have been cloned into /workspace "
                "and are on branch `agent/issue-{}`:\n\n"
            ).format(issue_number)
            for rc in repos:
                dir_name = rc.repo.split("/")[-1] if "/" in rc.repo else rc.repo
                context += f"- **{rc.repo}** → `/workspace/{dir_name}/`"
                if rc.description:
                    context += f"  — {rc.description}"
                context += "\n"
            context += (
                "\n**IMPORTANT:** All files you create or modify MUST be inside "
                "the repo directory (e.g. `/workspace/{}/`). Changes in these "
                "directories will be automatically committed and pushed after "
                "your work. Do NOT write files to `/workspace/` root.\n"
            ).format(repos[0].repo.split("/")[-1])

        return context

    @staticmethod
    def _assemble_prompt(
        issue: dict[str, Any],
        comments: list[dict[str, Any]],
        role: str,
        agents_dir: str,
        extra_context: str,
    ) -> str:
        """Assemble the final prompt from all parts."""
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
{extra_context}
---

Please execute the task and provide a summary of what you did."""

        return prompt
