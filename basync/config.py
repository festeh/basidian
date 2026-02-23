"""Config file loading for basync."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_EXCLUDES = [
    ".git",
    ".DS_Store",
    "node_modules",
    "__pycache__",
    ".env",
    "*.pyc",
    ".venv",
    "venv",
]


@dataclass
class BasyncConfig:
    """Configuration for basync."""

    backend_url: str = "http://localhost:8090"
    local_path: str = "."
    remote_path: str = "/"
    exclude: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDES.copy())
    include: list[str] = field(default_factory=list)


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find .basync.toml in current or parent directories."""
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()
    while current != current.parent:
        config_path = current / ".basync.toml"
        if config_path.exists():
            return config_path
        current = current.parent

    # Check root
    config_path = current / ".basync.toml"
    if config_path.exists():
        return config_path

    return None


def load_config(config_path: Optional[Path] = None) -> BasyncConfig:
    """Load config from file or return defaults."""
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        return BasyncConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    config = BasyncConfig()

    if "backend_url" in data:
        config.backend_url = data["backend_url"]
    if "local_path" in data:
        config.local_path = data["local_path"]
    if "remote_path" in data:
        config.remote_path = data["remote_path"]
    if "exclude" in data:
        config.exclude = data["exclude"]
    if "include" in data:
        config.include = data["include"]

    return config
