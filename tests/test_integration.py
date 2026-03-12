# tests/test_integration.py
"""
Integration tests for the full COGEMI pipeline.

Both the social-appropriateness and justice pipelines share identical
architecture — only the response labels and judgment map differ. A single
parameterised test exercises both dimensions to prove this symmetry.

All LLM calls use model="stub" so the suite runs without Ollama.
"""
import pytest
from typing import Dict, List

from cogemi.api import CogemiPipeline
from cogemi.observe.observation import Observation
from cogemi.observe.scenario import Scenario
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.survey.specification import SurveySpecification
from cogemi.survey.survey_response import SurveyResponse
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_pipeline(judgment_map: Dict[str, float]) -> CogemiPipeline:
    """Build a fully-stub pipeline for a given judgment map."""
    return CogemiPipeline(
        abstraction=TextAbstraction(model="stub"),
        survey_spec=SurveySpecification(
            instructions={"en": "Rate this."},
            response_labels=list(judgment_map.keys()),
        ),
        evaluator=HumanSurveyEvaluator(judgment_map=judgment_map, valid_responses=1),
        learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
        feature_extractor=LLMFeatureExtractor(model="stub"),
        generalizer=ContextLikelihoodModel(),
    )


def _assert_valid_distribution(dist: Dict) -> None:
    """Check that a distribution dict has keys -1/0/1 and sums to ~1."""
    assert set(dist.keys()) == {-1, 0, 1}, f"Unexpected keys: {set(dist.keys())}"
    total = sum(dist.values())
    assert abs(total - 1.0) < 1e-6, f"Distribution sums to {total}, not 1.0"
    assert all(0.0 <= v <= 1.0 for v in dist.values())


def _assert_valid_context_structure(contexts_dict: Dict) -> None:
    """Check that all context entries have required keys and valid distributions."""
    assert len(contexts_dict) >= 1
    for action, ctx_group in contexts_dict.items():
        assert isinstance(action, str)
        assert len(ctx_group) >= 1
        for label, entry in ctx_group.items():
            assert label.startswith("C"), f"Context label should start with 'C': {label}"
            assert "Distribution" in entry
            assert "Outcomes" in entry
            assert "States" in entry
            _assert_valid_distribution(entry["Distribution"])
            assert len(entry["Outcomes"]) >= 1
            assert len(entry["States"]) >= 1


def _responses(scenario_id: str, ratings: List[str]) -> List[SurveyResponse]:
    return [
        SurveyResponse(participant_id=f"p{i}", scenario_id=scenario_id, response=r)
        for i, r in enumerate(ratings)
    ]


# ---------------------------------------------------------------------------
# Parameterised integration test — same logic, two dimensions
# ---------------------------------------------------------------------------

APPROPRIATENESS = {
    "judgment_map": {"Inappropriate": -1, "Neutral": 0, "Appropriate": 1},
    # scenario_id format: prefix_action_state
    "scenarios": [
        Scenario(id="s_cutline_supermarket",
                 representation="Someone cuts in line at the supermarket.",
                 anchors={"action": "cutline"}, origin={}),
        Scenario(id="s_cutline_busstop",
                 representation="Someone cuts in front of an elderly person at the bus stop.",
                 anchors={"action": "cutline"}, origin={}),
        Scenario(id="s_holdoor_office",
                 representation="Someone holds the door open for a colleague.",
                 anchors={"action": "holdoor"}, origin={}),
        Scenario(id="s_holdoor_elevator",
                 representation="Someone holds the elevator for a person running late.",
                 anchors={"action": "holdoor"}, origin={}),
    ],
    # Strong negative signal for cutline, strong positive for holdoor
    "ratings_by_scenario": {
        "s_cutline_supermarket": ["Inappropriate", "Inappropriate", "Inappropriate", "Neutral", "Inappropriate"],
        "s_cutline_busstop":     ["Inappropriate", "Inappropriate", "Inappropriate", "Inappropriate", "Neutral"],
        "s_holdoor_office":      ["Appropriate",   "Appropriate",   "Appropriate",   "Neutral",       "Appropriate"],
        "s_holdoor_elevator":    ["Appropriate",   "Appropriate",   "Neutral",       "Appropriate",   "Appropriate"],
    },
    # Expected: cutline contexts skew negative, holdoor contexts skew positive
    "negative_action": "cutline",
    "positive_action": "holdoor",
}

JUSTICE = {
    "judgment_map": {"Unjust": -1, "Neutral": 0, "Just": 1},
    "scenarios": [
        Scenario(id="s_punishinnocent_court",
                 representation="A judge sentences an innocent person to improve crime statistics.",
                 anchors={"action": "punishinnocent"}, origin={}),
        Scenario(id="s_punishinnocent_school",
                 representation="A teacher punishes the whole class for one student's mistake.",
                 anchors={"action": "punishinnocent"}, origin={}),
        Scenario(id="s_protectchild_lie",
                 representation="A parent lies to protect their child from a dangerous stranger.",
                 anchors={"action": "protectchild"}, origin={}),
        Scenario(id="s_protectchild_hide",
                 representation="A parent hides their child from an abusive relative.",
                 anchors={"action": "protectchild"}, origin={}),
    ],
    "ratings_by_scenario": {
        "s_punishinnocent_court":  ["Unjust",   "Unjust",   "Unjust",   "Unjust",   "Neutral"],
        "s_punishinnocent_school": ["Unjust",   "Unjust",   "Unjust",   "Neutral",  "Unjust"],
        "s_protectchild_lie":      ["Just",     "Just",     "Just",     "Neutral",  "Just"],
        "s_protectchild_hide":     ["Just",     "Just",     "Neutral",  "Just",     "Just"],
    },
    "negative_action": "punishinnocent",
    "positive_action": "protectchild",
}


@pytest.mark.parametrize("spec", [APPROPRIATENESS, JUSTICE],
                         ids=["social_appropriateness", "justice"])
def test_pipeline_integration(spec):
    judgment_map = spec["judgment_map"]
    scenarios: List[Scenario] = spec["scenarios"]
    ratings_by_scenario: Dict[str, List[str]] = spec["ratings_by_scenario"]

    pipeline = _make_pipeline(judgment_map)

    # Build all survey responses
    survey_responses = []
    for scenario in scenarios:
        survey_responses.extend(
            _responses(scenario.id, ratings_by_scenario[scenario.id])
        )

    # --- fit ---
    pipeline.fit(scenarios, survey_responses)

    # --- contexts structure ---
    contexts = pipeline.contexts()
    _assert_valid_context_structure(contexts)

    # Both actions should be in the learned contexts
    assert spec["negative_action"] in contexts, (
        f"Expected action '{spec['negative_action']}' in contexts, got: {list(contexts.keys())}"
    )
    assert spec["positive_action"] in contexts, (
        f"Expected action '{spec['positive_action']}' in contexts, got: {list(contexts.keys())}"
    )

    # --- distribution polarity ---
    # The context for the clearly negative action should skew negative (p(-1) > p(1))
    neg_dist = list(contexts[spec["negative_action"]].values())[0]["Distribution"]
    assert neg_dist[-1] > neg_dist[1], (
        f"Expected negative skew for '{spec['negative_action']}': {neg_dist}"
    )

    # The context for the clearly positive action should skew positive (p(1) > p(-1))
    pos_dist = list(contexts[spec["positive_action"]].values())[0]["Distribution"]
    assert pos_dist[1] > pos_dist[-1], (
        f"Expected positive skew for '{spec['positive_action']}': {pos_dist}"
    )

    # --- predict (full cycle with stub abstraction) ---
    obs = Observation(
        id="obs_new",
        modalities={"text": "Someone takes the last seat without asking."},
        metadata={},
    )
    prediction = pipeline.predict(obs)

    assert isinstance(prediction, dict)
    assert len(prediction) >= 1
    assert abs(sum(prediction.values()) - 1.0) < 1e-6, (
        f"predict_proba should sum to 1.0, got {sum(prediction.values())}"
    )


# ---------------------------------------------------------------------------
# Additional targeted checks
# ---------------------------------------------------------------------------

def test_map_responses_preserves_order_and_count():
    """map_responses_to_samples should group by scenario and preserve response order."""
    pipeline = _make_pipeline({"Unjust": -1, "Neutral": 0, "Just": 1})
    responses = [
        SurveyResponse("p1", "s_a_1", "Just"),
        SurveyResponse("p2", "s_a_1", "Neutral"),
        SurveyResponse("p3", "s_b_2", "Unjust"),
        SurveyResponse("p4", "s_b_2", "Unjust"),
        SurveyResponse("p5", "s_b_2", "Just"),
    ]
    samples = pipeline.map_responses_to_samples(responses)

    assert len(samples) == 2          # two distinct scenario IDs
    assert samples[0] == [1, 0]       # s_a_1
    assert samples[1] == [-1, -1, 1]  # s_b_2


def test_fit_returns_context_label_per_scenario():
    """ContextLearner.fit() must return exactly one label per scenario."""
    learner = ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js")
    scenarios = [
        Scenario(id="s_actionA_s1", representation="Scenario A1", anchors={}, origin={}),
        Scenario(id="s_actionA_s2", representation="Scenario A2", anchors={}, origin={}),
        Scenario(id="s_actionB_s1", representation="Scenario B1", anchors={}, origin={}),
    ]
    samples = [[-1, -1, 0], [1, 1, 0], [-1, -1, -1]]

    labels = learner.fit(scenarios, samples)

    assert len(labels) == 3
    assert all(isinstance(l, str) and ":" in l for l in labels)
    # Labels should reference the action segment of the scenario ID
    assert labels[0].startswith("actionA:")
    assert labels[1].startswith("actionA:")
    assert labels[2].startswith("actionB:")
