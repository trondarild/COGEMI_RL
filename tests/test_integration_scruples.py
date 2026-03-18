# tests/test_integration_scruples.py
"""
Integration test: SCRUPLES Anecdotes loader → full COGEMI pipeline.

Uses a small sample from the train split so the test is fast.
All LLM calls use model="stub".

Skips automatically if the SCRUPLES train file is not present.
"""
import pytest
from pathlib import Path

from cogemi.api import CogemiPipeline
from cogemi.data.scruples import (
    load_anecdotes,
    load_justice_subset,
    JUDGMENT_MAP,
    JUSTICE_JUDGMENT_MAP,
)
from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.observe.text_abstraction import TextAbstraction

SCRUPLES_TRAIN = (
    Path(__file__).parent.parent / "data" / "anecdotes" / "train.scruples-anecdotes.jsonl"
)

pytestmark = pytest.mark.skipif(
    not SCRUPLES_TRAIN.exists(),
    reason="SCRUPLES train split not found — download dataset first",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pipeline(judgment_map: dict) -> CogemiPipeline:
    return CogemiPipeline(
        abstraction=TextAbstraction(model="stub"),
        survey_spec=SurveySpecification(
            instructions={"en": "Rate this action."},
            response_labels=list(judgment_map.keys()),
        ),
        evaluator=HumanSurveyEvaluator(
            judgment_map=judgment_map,
            valid_responses=1,
        ),
        learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
        feature_extractor=LLMFeatureExtractor(model="stub"),
        generalizer=ContextLikelihoodModel(),
    )


# ---------------------------------------------------------------------------
# load_anecdotes tests
# ---------------------------------------------------------------------------

def test_load_anecdotes_types():
    scenarios, responses = load_anecdotes(SCRUPLES_TRAIN, max_records=100)
    assert isinstance(scenarios, list)
    assert isinstance(responses, list)
    assert len(scenarios) >= 1
    assert len(responses) >= len(scenarios)

    s = scenarios[0]
    assert isinstance(s, Scenario)
    assert s.id.startswith("sc_")
    parts = s.id.split("_")
    assert len(parts) == 3, f"Expected 3 ID parts, got: {s.id}"
    assert "action" in s.anchors

    r = responses[0]
    assert isinstance(r, SurveyResponse)
    assert r.response in JUDGMENT_MAP


def test_load_anecdotes_ids_unique():
    scenarios, _ = load_anecdotes(SCRUPLES_TRAIN, max_records=200)
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), "Duplicate scenario IDs"


def test_load_anecdotes_responses_reference_scenarios():
    scenarios, responses = load_anecdotes(SCRUPLES_TRAIN, max_records=100)
    scenario_ids = {s.id for s in scenarios}
    for r in responses:
        assert r.scenario_id in scenario_ids


def test_load_anecdotes_min_votes():
    s3, _ = load_anecdotes(SCRUPLES_TRAIN, min_votes=3, max_records=500)
    s10, _ = load_anecdotes(SCRUPLES_TRAIN, min_votes=10, max_records=500)
    assert len(s3) >= len(s10)


def test_load_anecdotes_max_votes_per_side_cap():
    _, responses_cap = load_anecdotes(
        SCRUPLES_TRAIN, max_votes_per_side=5, max_records=200
    )
    _, responses_no_cap = load_anecdotes(
        SCRUPLES_TRAIN, max_votes_per_side=1000, max_records=200
    )
    assert len(responses_cap) <= len(responses_no_cap)


# ---------------------------------------------------------------------------
# load_justice_subset tests
# ---------------------------------------------------------------------------

def test_load_justice_subset_types():
    scenarios, responses = load_justice_subset(SCRUPLES_TRAIN, max_records=50)
    assert len(scenarios) >= 1

    s = scenarios[0]
    assert s.id.startswith("scj_")
    parts = s.id.split("_")
    assert len(parts) == 3, f"Expected 3 ID parts, got: {s.id}"
    assert s.roles is not None
    assert "agent" in s.roles
    assert "target" in s.roles

    for r in responses:
        assert r.response in JUSTICE_JUDGMENT_MAP
        assert r.role_perspective == "observer"


def test_load_justice_subset_smaller_than_full():
    s_full, _ = load_anecdotes(SCRUPLES_TRAIN, max_records=500)
    s_justice, _ = load_justice_subset(SCRUPLES_TRAIN, max_records=500)
    assert len(s_justice) <= len(s_full)


def test_load_justice_subset_ids_unique():
    scenarios, _ = load_justice_subset(SCRUPLES_TRAIN, max_records=200)
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), "Duplicate scenario IDs"


def test_load_justice_subset_responses_reference_scenarios():
    scenarios, responses = load_justice_subset(SCRUPLES_TRAIN, max_records=100)
    scenario_ids = {s.id for s in scenarios}
    for r in responses:
        assert r.scenario_id in scenario_ids


# ---------------------------------------------------------------------------
# Pipeline integration: load_justice_subset → fit → predict
# ---------------------------------------------------------------------------

def test_scruples_justice_pipeline_fit_and_contexts():
    scenarios, responses = load_justice_subset(
        SCRUPLES_TRAIN, min_votes=5, max_records=200
    )
    assert len(scenarios) >= 1

    pipeline = _make_pipeline(JUSTICE_JUDGMENT_MAP)
    pipeline.fit(scenarios, responses)

    contexts = pipeline.contexts()
    assert isinstance(contexts, dict)
    assert len(contexts) >= 1

    # When role_perspective is set, contexts() returns Dict[role, ContextsDict].
    # Flatten one level to get a plain ContextsDict for validation.
    first_value = next(iter(contexts.values()))
    if isinstance(first_value, dict) and isinstance(next(iter(first_value.values())), dict):
        # role-indexed: {role: {action: {label: entry}}}
        role_contexts = {role: cd for role, cd in contexts.items()}
        for role, cd in role_contexts.items():
            for action, ctx_group in cd.items():
                for label, entry in ctx_group.items():
                    assert "Distribution" in entry, (
                        f"Missing 'Distribution' in entry for role={role}, action={action}, label={label}"
                    )
                    dist = entry["Distribution"]
                    assert set(dist.keys()) == {-1, 0, 1}
                    assert abs(sum(dist.values()) - 1.0) < 1e-6
    else:
        # non-role: {action: {label: entry}}
        for action, ctx_group in contexts.items():
            for label, entry in ctx_group.items():
                assert "Distribution" in entry
                dist = entry["Distribution"]
                assert set(dist.keys()) == {-1, 0, 1}
                assert abs(sum(dist.values()) - 1.0) < 1e-6


def test_scruples_justice_pipeline_predict():
    from cogemi.observe.observation import Observation

    scenarios, responses = load_justice_subset(
        SCRUPLES_TRAIN, min_votes=5, max_records=200
    )
    pipeline = _make_pipeline(JUSTICE_JUDGMENT_MAP)
    pipeline.fit(scenarios, responses)

    obs = Observation(
        id="obs_scj_test",
        modalities={"text": "An employer withholds overtime pay from a worker."},
        metadata={},
    )
    prediction = pipeline.predict(obs)

    assert isinstance(prediction, dict)
    assert len(prediction) >= 1
    assert abs(sum(prediction.values()) - 1.0) < 1e-6
