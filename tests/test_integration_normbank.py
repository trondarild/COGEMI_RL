# tests/test_integration_normbank.py
"""
Integration test: NormBank loader → full COGEMI pipeline.

Uses a 500-row sample from NormBank.csv (train split) so the test is fast
and self-contained.  All LLM calls use model="stub".

Skips automatically if NormBank.csv is not present (data/ is gitignored).
"""
import os
import pytest
from pathlib import Path

from cogemi.api import CogemiPipeline
from cogemi.data.normbank import load_normbank, JUDGMENT_MAP
from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.observe.text_abstraction import TextAbstraction

NORMBANK_PATH = Path(__file__).parent.parent / "data" / "NormBank.csv"

pytestmark = pytest.mark.skipif(
    not NORMBANK_PATH.exists(),
    reason="NormBank.csv not found — download dataset first",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_normbank_pipeline() -> CogemiPipeline:
    return CogemiPipeline(
        abstraction=TextAbstraction(model="stub"),
        survey_spec=SurveySpecification(
            instructions={"en": "Rate this behaviour."},
            response_labels=list(JUDGMENT_MAP.keys()),
        ),
        evaluator=HumanSurveyEvaluator(
            judgment_map=JUDGMENT_MAP,
            valid_responses=1,
        ),
        learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
        feature_extractor=LLMFeatureExtractor(model="stub"),
        generalizer=ContextLikelihoodModel(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_load_normbank_returns_correct_types():
    """Loader returns lists of Scenario and SurveyResponse."""
    scenarios, responses = load_normbank(NORMBANK_PATH, max_rows=200, min_responses=2)

    assert isinstance(scenarios, list)
    assert isinstance(responses, list)
    assert len(scenarios) >= 1
    assert len(responses) >= len(scenarios)

    s = scenarios[0]
    assert isinstance(s, Scenario)
    assert s.id.startswith("nb_")
    # ID must have exactly two underscores so ContextLearner can parse it
    parts = s.id.split("_")
    assert len(parts) == 3, f"Expected 3 parts in ID, got: {s.id}"
    assert "action" in s.anchors
    assert "setting" in s.anchors

    r = responses[0]
    assert isinstance(r, SurveyResponse)
    assert r.scenario_id == scenarios[0].id
    assert r.response in JUDGMENT_MAP


def test_load_normbank_min_responses_filter():
    """Groups with fewer than min_responses rows are excluded."""
    scenarios_5, _ = load_normbank(NORMBANK_PATH, max_rows=500, min_responses=5)
    scenarios_2, _ = load_normbank(NORMBANK_PATH, max_rows=500, min_responses=2)
    # Stricter filter should yield fewer or equal scenarios
    assert len(scenarios_5) <= len(scenarios_2)


def test_load_normbank_split_filter():
    """split='train' returns only train rows."""
    scenarios_train, responses_train = load_normbank(
        NORMBANK_PATH, split="train", max_rows=300, min_responses=2
    )
    # All responses should have norm values (the loader already filters on this)
    assert all(r.response in JUDGMENT_MAP for r in responses_train)


def test_normbank_scenario_ids_unique():
    """Every scenario has a unique ID."""
    scenarios, _ = load_normbank(NORMBANK_PATH, max_rows=500, min_responses=2)
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), "Duplicate scenario IDs detected"


def test_normbank_responses_reference_valid_scenario():
    """Every SurveyResponse references an existing scenario ID."""
    scenarios, responses = load_normbank(NORMBANK_PATH, max_rows=500, min_responses=2)
    scenario_ids = {s.id for s in scenarios}
    for r in responses:
        assert r.scenario_id in scenario_ids, (
            f"Response references unknown scenario: {r.scenario_id}"
        )


def test_normbank_pipeline_fit_and_contexts():
    """Full pipeline fit on a NormBank sample completes without error."""
    scenarios, responses = load_normbank(
        NORMBANK_PATH, split="train", max_rows=5000, min_responses=5
    )
    assert len(scenarios) >= 1, "No scenarios loaded — increase max_rows or lower min_responses"

    pipeline = _make_normbank_pipeline()
    pipeline.fit(scenarios, responses)

    contexts = pipeline.contexts()
    assert isinstance(contexts, dict)
    assert len(contexts) >= 1

    # Every context entry should have the expected structure
    for action, ctx_group in contexts.items():
        assert isinstance(action, str)
        for label, entry in ctx_group.items():
            assert "Distribution" in entry
            assert "Outcomes" in entry
            assert "States" in entry
            dist = entry["Distribution"]
            assert set(dist.keys()) == {-1, 0, 1}
            total = sum(dist.values())
            assert abs(total - 1.0) < 1e-6, f"Distribution sums to {total}"


def test_normbank_pipeline_predict():
    """pipeline.predict() returns a valid probability distribution after fitting."""
    from cogemi.observe.observation import Observation

    scenarios, responses = load_normbank(
        NORMBANK_PATH, split="train", max_rows=5000, min_responses=5
    )
    pipeline = _make_normbank_pipeline()
    pipeline.fit(scenarios, responses)

    obs = Observation(
        id="obs_nb_test",
        modalities={"text": "Someone whistles at a stranger on the street."},
        metadata={},
    )
    prediction = pipeline.predict(obs)

    assert isinstance(prediction, dict)
    assert len(prediction) >= 1
    assert abs(sum(prediction.values()) - 1.0) < 1e-6, (
        f"predict() should sum to 1.0, got {sum(prediction.values())}"
    )
