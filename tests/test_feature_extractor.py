# tests/test_feature_extractor.py
import pytest
import urllib.request

from cogemi.features.extractor_llm import LLMFeatureExtractor, extract_action, _parse_csv_list
from cogemi.observe.scenario import Scenario


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:
        return False


requires_ollama = pytest.mark.skipif(
    not _ollama_available(), reason="Ollama not running"
)


# ---------------------------------------------------------------------------
# Stub mode tests (always run, no LLM needed)
# ---------------------------------------------------------------------------

def test_stub_extract_from_scenarios():
    extractor = LLMFeatureExtractor(model="stub")
    scenarios = [
        Scenario(id="c1", representation="Someone politely corrects another person.",
                 anchors={"action": "polite_correction"}, origin={}),
        Scenario(id="c2", representation="Someone publicly shames another person.",
                 anchors={"action": "public_shaming"}, origin={}),
    ]
    features = extractor.extract_from_scenarios(scenarios)

    assert len(features) == 2
    assert all(isinstance(f, list) for f in features)
    assert all(len(f) > 0 for f in features)
    assert all(isinstance(item, str) for f in features for item in f)


def test_stub_extract_action():
    assert isinstance(extract_action("Someone cuts in line.", model="stub"), str)


def test_parse_csv_list_basic():
    raw = "Protective intent, Deception for personal gain, Respect for autonomy"
    result = _parse_csv_list(raw)
    assert result == ["Protective intent", "Deception for personal gain", "Respect for autonomy"]


def test_parse_csv_list_strips_thinking_tags():
    raw = "<think>some reasoning</think>Protective intent, Deception for personal gain"
    result = _parse_csv_list(raw)
    assert "Protective intent" in result
    assert not any("<think>" in item for item in result)


def test_parse_csv_list_single_item_fallback():
    raw = "Protective intent"
    result = _parse_csv_list(raw)
    assert result == ["Protective intent"]


# ---------------------------------------------------------------------------
# Live Ollama tests (skipped when Ollama is not running)
# ---------------------------------------------------------------------------

@requires_ollama
def test_ollama_extract_action():
    extractor = LLMFeatureExtractor(model="qwen3:1.7b")
    text = "A mother lies to her child about Santa Claus to preserve the magic of Christmas."
    action = extractor.extract_action(text)

    assert isinstance(action, str)
    assert len(action) > 5
    # Should start with "To " (generalised action form)
    assert action.lower().startswith("to "), f"Unexpected action format: {action!r}"


@requires_ollama
def test_ollama_extract_from_scenario():
    extractor = LLMFeatureExtractor(model="qwen3:1.7b")
    scenario = Scenario(
        id="s1",
        representation="A nurse tells an elderly patient that their family is 'just running late' every day, even though no one is visiting.",
        anchors={},
        origin={},
    )
    features = extractor.extract_from_scenario(scenario)

    assert isinstance(features, list)
    assert len(features) >= 1
    assert all(isinstance(f, str) and len(f) > 2 for f in features)


@requires_ollama
def test_ollama_module_level_extract_action():
    action = extract_action("A manager fires an employee to make room for a friend.", model="qwen3:1.7b")
    assert isinstance(action, str)
    assert action.lower().startswith("to ")
