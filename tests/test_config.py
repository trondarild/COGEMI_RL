# tests/test_config.py
import os
import tempfile
from pathlib import Path

import pytest

from cogemi.config import load_config, CogemiConfig, LLMConfig
from cogemi.features.extractor_llm import LLMFeatureExtractor


# ---------------------------------------------------------------------------
# load_config() — defaults when no file present
# ---------------------------------------------------------------------------

def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # ensure no cogemi_config.yaml in cwd
    monkeypatch.delenv("COGEMI_CONFIG", raising=False)
    monkeypatch.delenv("COGEMI_API_KEY", raising=False)

    cfg = load_config()

    assert isinstance(cfg, CogemiConfig)
    assert cfg.llm.provider == "ollama"
    assert cfg.llm.model == "qwen3:1.7b"
    assert cfg.llm.base_url == "http://localhost:11434"
    assert cfg.llm.api_key is None


# ---------------------------------------------------------------------------
# load_config() — reads values from a YAML file
# ---------------------------------------------------------------------------

def test_reads_yaml_file(tmp_path):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text(
        "llm:\n"
        "  provider: openai\n"
        "  model: gpt-4o-mini\n"
        "  base_url: https://api.openai.com/v1\n"
        "  api_key: test-key\n"
    )

    cfg = load_config(config_file)

    assert cfg.llm.provider == "openai"
    assert cfg.llm.model == "gpt-4o-mini"
    assert cfg.llm.base_url == "https://api.openai.com/v1"
    assert cfg.llm.api_key == "test-key"


def test_env_var_overrides_file_api_key(tmp_path, monkeypatch):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text("llm:\n  provider: openai\n  api_key: from-file\n")
    monkeypatch.setenv("COGEMI_API_KEY", "from-env")

    cfg = load_config(config_file)

    assert cfg.llm.api_key == "from-env"


def test_cogemi_config_env_var(tmp_path, monkeypatch):
    config_file = tmp_path / "custom.yaml"
    config_file.write_text("llm:\n  model: gemma3:1b\n")
    monkeypatch.setenv("COGEMI_CONFIG", str(config_file))
    monkeypatch.chdir(tmp_path)  # no cogemi_config.yaml in cwd

    cfg = load_config()

    assert cfg.llm.model == "gemma3:1b"


def test_empty_yaml_uses_defaults(tmp_path):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text("")  # empty file

    cfg = load_config(config_file)

    assert cfg.llm.provider == "ollama"
    assert cfg.llm.model == "qwen3:1.7b"


# ---------------------------------------------------------------------------
# LLMFeatureExtractor — picks up config
# ---------------------------------------------------------------------------

def test_extractor_reads_model_from_config(tmp_path):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text("llm:\n  provider: ollama\n  model: gemma3:1b\n")

    extractor = LLMFeatureExtractor(config_path=str(config_file))

    assert extractor.model == "gemma3:1b"
    assert extractor.llm_config.provider == "ollama"


def test_extractor_model_arg_overrides_config(tmp_path):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text("llm:\n  model: gemma3:1b\n")

    extractor = LLMFeatureExtractor(model="stub", config_path=str(config_file))

    assert extractor.model == "stub"  # explicit arg wins


def test_extractor_unknown_provider_raises(tmp_path):
    config_file = tmp_path / "cogemi_config.yaml"
    config_file.write_text("llm:\n  provider: anthropic\n  model: claude-3\n")

    extractor = LLMFeatureExtractor(config_path=str(config_file))

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        extractor._call("hello")
