"""Workflow service — YAML loading, phase navigation, and workflow transitions."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import json

from domain.workflow import BranchRule, Phase, RepoConfig, Workflow
from ports.github_port import GitHubPort

logger = logging.getLogger(__name__)

# PyYAML is not in stdlib; try import, fallback to json.
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# YAML parsing helpers
# ---------------------------------------------------------------------------

def _parse_yaml(path: str) -> dict[str, Any]:
    """Parse a YAML file. Uses PyYAML if available, otherwise json fallback."""
    if yaml is not None:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        import json
        with open(path, "r") as f:
            return json.load(f)


def _parse_repos(raw_list: list[dict[str, Any]]) -> list[RepoConfig]:
    """Parse the ``config`` list into RepoConfig objects."""
    repos: list[RepoConfig] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        repos.append(RepoConfig(
            repo=item.get("repo", ""),
            url=item.get("url", ""),
            description=item.get("description", ""),
        ))
    return repos


def _parse_branchs(raw_list: list[dict[str, Any]]) -> list[BranchRule]:
    """Parse a list of branch-rule dicts into BranchRule objects.

    Each dict MUST have a ``target`` key.  Every other key-value pair in the
    dict is treated as a condition that must match a branch-var.
    """
    rules: list[BranchRule] = []
    for item in raw_list:
        if not isinstance(item, dict) or "target" not in item:
            continue
        target = str(item["target"])
        conditions = {str(k): str(v) for k, v in item.items() if k != "target"}
        rules.append(BranchRule(target=target, conditions=conditions))
    return rules


def _parse_phases(raw_list: list[dict[str, Any]]) -> list[Phase]:
    """Parse a list of phase dicts into Phase objects."""
    phases: list[Phase] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        # phase-env: dict of extra env vars for hook scripts
        raw_env = item.get("phase-env", {}) or {}
        phase_env = {str(k): str(v) for k, v in raw_env.items()} if isinstance(raw_env, dict) else {}
        # branchs: required list of branch rules
        raw_branchs = item.get("branchs", []) or []
        branchs = _parse_branchs(raw_branchs) if isinstance(raw_branchs, list) else []
        phases.append(Phase(
            role=item.get("role", ""),
            phasename=item.get("phasename", ""),
            phase_prompt=item.get("phase-prompt", "") or "",
            llm_model=item.get("llm-model", ""),
            workspace_init=item.get("workspace-init", []) or [],
            workspace_cleanup=item.get("workspace-cleanup", []) or [],
            phase_env=phase_env,
            branchs=branchs,
        ))
    return phases


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class WorkflowService:
    """Manages workflow loading, phase resolution, and phase transitions."""

    def __init__(self, github_port: GitHubPort):
        self.github = github_port

    # --- Loading ---

    def load_workflows(self, workflow_file: str) -> dict[str, Workflow]:
        """Load all workflows from a YAML file.

        Supports two formats:

        **New format (config + steps):**

            workflowA:
              config:
                - repo: owner/repo
              steps:
                - role: manager
                  phasename: requirement-analysis
                  ...

        **Legacy format (flat list of phases):**

            workflowA:
              - role: manager
                phasename: requirement-analysis
                ...
        """
        if not workflow_file or not os.path.isfile(workflow_file):
            logger.info(
                "No workflow file found at '%s', workflow features disabled",
                workflow_file,
            )
            return {}

        try:
            raw = _parse_yaml(workflow_file)
        except Exception as e:
            logger.error("Failed to parse workflow file '%s': %s", workflow_file, e)
            return {}

        workflows: dict[str, Workflow] = {}
        for wf_name, wf_data in raw.items():
            if isinstance(wf_data, list):
                # Legacy format
                phases = _parse_phases(wf_data)
                repos: list[RepoConfig] = []
            elif isinstance(wf_data, dict):
                # New format
                repos = _parse_repos(wf_data.get("config", []) or [])
                phases = _parse_phases(wf_data.get("steps", []) or [])
            else:
                logger.warning("Workflow '%s' has unexpected type, skipping", wf_name)
                continue

            workflows[wf_name] = Workflow(name=wf_name, repos=repos, phases=phases)
            logger.info(
                "Loaded workflow '%s' with %d repos, %d phases",
                wf_name, len(repos), len(phases),
            )

        return workflows

    # --- Phase env builder ---

    @staticmethod
    def build_phase_env(
        workflow: Workflow,
        phase: Phase,
        issue_number: int,
        issue_repo: str,
    ) -> dict[str, str]:
        """Build the environment variables dict for hook scripts.

        Combines computed values (REPOS, ISSUE_NUMBER, BRANCH_NAME, etc.)
        with user-defined phase-env from the workflow YAML.
        YAML phase-env values take precedence over computed defaults.
        """
        branch = f"agent/issue-{issue_number}"
        repos_json = json.dumps(
            [{"repo": rc.repo, "url": rc.url, "description": rc.description}
             for rc in workflow.repos]
        )

        computed: dict[str, str] = {
            "REPOS": repos_json,
            "ISSUE_NUMBER": str(issue_number),
            "BRANCH_NAME": branch,
            "ISSUE_REPO": issue_repo,
            "PHASE_NAME": phase.phasename,
        }
        # YAML phase-env overrides computed defaults
        computed.update(phase.phase_env)
        return computed

    # --- Phase navigation ---

    def find_phase_by_label(self, workflow: Workflow, phase_label: str) -> Optional[int]:
        """Find phase index by phasename."""
        for i, phase in enumerate(workflow.phases):
            if phase.phasename == phase_label:
                return i
        return None

    def get_next_phase(self, workflow: Workflow, current_index: int) -> Optional[Phase]:
        """Return the next phase after current_index, or None if last."""
        next_idx = current_index + 1
        if next_idx < len(workflow.phases):
            return workflow.phases[next_idx]
        return None

    # --- Phase resolution ---

    def resolve_phase(
        self,
        workflow: Workflow,
        phase_name: str | None,
        repo: str,
        issue_number: int,
    ) -> tuple[int | None, Phase | None]:
        """Resolve the current phase index and Phase object.

        If phase_name is given, looks it up. Otherwise defaults to the first
        phase and auto-adds the phase label.

        Returns:
            (phase_idx, phase) — both None if workflow has no phases.
        """
        phase_idx: int | None = None

        if phase_name:
            phase_idx = self.find_phase_by_label(workflow, phase_name)
            if phase_idx is None:
                logger.warning(
                    "Issue #%d: phase '%s' not found in workflow '%s', "
                    "falling back to first phase",
                    issue_number, phase_name, workflow.name,
                )

        # Default to first phase if not found or not specified
        if phase_idx is None and workflow.phases:
            phase_idx = 0
            first_phase = workflow.phases[0]
            logger.info(
                "Issue #%d: defaulting to first phase '%s' of workflow '%s'",
                issue_number, first_phase.phasename, workflow.name,
            )
            # Auto-add role + phase labels for tracking
            try:
                self.github.add_label(repo, issue_number, f"role:{first_phase.role}")
                self.github.add_label(repo, issue_number, f"phase:{first_phase.phasename}")
            except Exception as e:
                logger.warning("Issue #%d: failed to auto-add labels: %s", issue_number, e)

        if phase_idx is not None:
            return phase_idx, workflow.phases[phase_idx]
        return None, None

    # --- Branch evaluation ---

    @staticmethod
    def read_branch_vars(vars_file: str = "/workspace/.branch-vars") -> dict[str, str]:
        """Read branch variables from the well-known file.

        The file uses ``KEY=VALUE`` lines (``#`` comments and blanks ignored).
        """
        result: dict[str, str] = {}
        try:
            with open(vars_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        result[key.strip()] = value.strip()
        except FileNotFoundError:
            pass
        return result

    @staticmethod
    def evaluate_branches(
        branchs: list["BranchRule"],
        branch_vars: dict[str, str],
    ) -> str:
        """Evaluate branch rules against branch variables.

        Rules are checked in order; the first rule whose *all* conditions
        match wins.  A rule with no conditions is an unconditional default.

        Returns the ``target`` phasename (or ``"end"``).
        """
        for rule in branchs:
            if not rule.conditions:
                return rule.target          # unconditional default
            if all(branch_vars.get(k) == v for k, v in rule.conditions.items()):
                return rule.target
        # Shouldn't reach here if YAML always has a default, but be safe
        return "end"

    # --- Phase transition ---

    def transition_to_phase(
        self,
        workflow: Workflow,
        current_phase: Phase,
        target_name: str,
        repo: str,
        issue_number: int,
    ) -> None:
        """Transition from *current_phase* to the phase identified by *target_name*.

        ``target_name`` may be a phasename or the special value ``"end"``.
        If the target equals the current phase (retry), labels are left unchanged.
        """
        # Retry — no label change needed; next poll will re-process
        if target_name == current_phase.phasename:
            logger.info(
                "Issue #%d: branch target is current phase '%s' (retry)",
                issue_number, target_name,
            )
            return

        # Remove current role + phase labels
        try:
            self.github.remove_label(repo, issue_number, f"role:{current_phase.role}")
        except Exception:
            pass
        try:
            self.github.remove_label(repo, issue_number, f"phase:{current_phase.phasename}")
        except Exception:
            pass

        # target: end
        if target_name == "end":
            self.github.add_label(repo, issue_number, "phase:end")
            logger.info(
                "Issue #%d: workflow '%s' completed (branch target=end), set phase:end",
                issue_number, workflow.name,
            )
            return

        # Find target phase in workflow
        target_phase = next(
            (p for p in workflow.phases if p.phasename == target_name), None,
        )
        if target_phase is None:
            logger.error(
                "Issue #%d: branch target '%s' not found in workflow '%s', "
                "setting phase:end as safety fallback",
                issue_number, target_name, workflow.name,
            )
            self.github.add_label(repo, issue_number, "phase:end")
            return

        self.github.add_label(repo, issue_number, f"role:{target_phase.role}")
        self.github.add_label(repo, issue_number, f"phase:{target_name}")
        logger.info(
            "Issue #%d: branching to phase '%s' (role:%s)",
            issue_number, target_name, target_phase.role,
        )
