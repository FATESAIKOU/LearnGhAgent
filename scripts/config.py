"""Configuration management — reads environment variables."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    target_repo: str
    poll_interval: int
    agent_timeout: int
    copilot_model: str
    default_role: str
    state_file: str
    agents_dir: str

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

    return Config(
        target_repo=target_repo,
        poll_interval=int(os.environ.get("POLL_INTERVAL", "60")),
        agent_timeout=int(os.environ.get("AGENT_TIMEOUT", "900")),
        copilot_model=os.environ.get("COPILOT_MODEL", ""),
        default_role=os.environ.get("DEFAULT_ROLE", "default"),
        state_file=os.environ.get("STATE_FILE", "/data/state.json"),
        agents_dir=os.environ.get("AGENTS_DIR", "/app/agents"),
    )
