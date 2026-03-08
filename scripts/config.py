"""Configuration management — reads environment variables."""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    target_repo: str
    poll_interval: int
    agent_timeout: int
    copilot_model: str
    default_role: str
    agents_dir: str
    enabled_agents: list[str] = field(default_factory=list)
    workflow_file: str = ""

    @property
    def owner(self) -> str:
        return self.target_repo.split("/")[0]

    @property
    def repo(self) -> str:
        return self.target_repo.split("/")[1]


def load_config() -> Config:
    target_repo = os.environ.get("TARGET_REPO", "")
    if not target_repo or "/" not in target_repo:
        raise ValueError("TARGET_REPO must be set in 'owner/repo' format")

    # ENABLED_AGENTS: comma-separated list of agent names, empty = all
    enabled_raw = os.environ.get("ENABLED_AGENTS", "").strip()
    enabled_agents = [a.strip() for a in enabled_raw.split(",") if a.strip()] if enabled_raw else []

    return Config(
        target_repo=target_repo,
        poll_interval=int(os.environ.get("POLL_INTERVAL", "60")),
        agent_timeout=int(os.environ.get("AGENT_TIMEOUT", "900")),
        copilot_model=os.environ.get("COPILOT_MODEL", ""),
        default_role=os.environ.get("DEFAULT_ROLE", "default"),
        agents_dir=os.environ.get("AGENTS_DIR", "/app/agents"),
        enabled_agents=enabled_agents,
        workflow_file=os.environ.get("WORKFLOW_FILE", "/app/workflows/default.yml"),
    )
