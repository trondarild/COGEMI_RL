# cogemi/config.py
"""
Load LLM provider/model configuration from a YAML file.

Search order (first found wins):
  1. Path passed explicitly to load_config()
  2. COGEMI_CONFIG env var
  3. cogemi_config.yaml in current working directory
  4. ~/.cogemi_config.yaml

If no file is found, built-in defaults are used (ollama / qwen3:1.7b).

Example cogemi_config.yaml:
  llm:
    provider: ollama          # ollama | openai
    model: qwen3:1.7b
    base_url: http://localhost:11434
    # api_key: ""             # for openai-compatible APIs; or set COGEMI_API_KEY
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_DEFAULT_SEARCH = [
    Path("cogemi_config.yaml"),
    Path.home() / ".cogemi_config.yaml",
]


@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "qwen3:1.7b"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None


@dataclass
class CogemiConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)


def load_config(path: Optional[str | Path] = None) -> CogemiConfig:
    """Load and return a CogemiConfig.

    Falls back to defaults if no config file is found.
    """
    resolved = _resolve_path(path)

    if resolved is None:
        return CogemiConfig()

    with open(resolved) as f:
        raw = yaml.safe_load(f) or {}

    llm_raw = raw.get("llm", {})

    # api_key: prefer env var over file value
    api_key = os.environ.get("COGEMI_API_KEY") or llm_raw.get("api_key")

    llm = LLMConfig(
        provider=llm_raw.get("provider", "ollama"),
        model=llm_raw.get("model", "qwen3:1.7b"),
        base_url=llm_raw.get("base_url", "http://localhost:11434"),
        api_key=api_key,
    )
    return CogemiConfig(llm=llm)


def _resolve_path(path: Optional[str | Path]) -> Optional[Path]:
    """Return the first existing config file path, or None."""
    candidates: list[Path] = []

    if path is not None:
        candidates.append(Path(path))

    env = os.environ.get("COGEMI_CONFIG")
    if env:
        candidates.append(Path(env))

    candidates.extend(_DEFAULT_SEARCH)

    for p in candidates:
        if p.exists():
            return p

    return None
