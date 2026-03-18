# tests/test_integration_role.py
"""
Integration tests for the role-aware COGEMI pipeline using the synthetic
test role dataset (100 scenarios × 3 roles).

All LLM calls use model="stub".  The synthetic response distributions are
tuned so that:
  - exploit / deceive / coerce / discriminate  → unjust from target/observer view,
                                                  just from agent view (self-serving)
  - protect / compensate / advocate / assist   → just from all roles
  - discipline / compete                       → ambiguous (mixed distributions)

Tests verify the full pipeline cycle:
  fit → contexts structure → distribution polarity → predict
"""
import pytest
from typing import Dict

from cogemi.api import CogemiPipeline
from cogemi.observe.observation import Observation
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel

from cogemi.data.test_role_dataset import (
    load_test_role_dataset,
    JUDGMENT_MAP,
    action_names,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ROLE_INSTRUCTIONS = {
    "agent": {"en": "You are the agent. How just is what you are doing?"},
    "target": {"en": "You are the target. How just is what is being done to you?"},
    "observer": {"en": "You are an observer. How just is the agent's action?"},
}


def _make_pipeline() -> CogemiPipeline:
    return CogemiPipeline(
        abstraction=TextAbstraction(model="stub"),
        survey_spec=SurveySpecification(
            instructions={"en": "How just is this action?"},
            response_labels=list(JUDGMENT_MAP.keys()),
            role_instructions=ROLE_INSTRUCTIONS,
        ),
        evaluator=HumanSurveyEvaluator(judgment_map=JUDGMENT_MAP, valid_responses=1),
        learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
        feature_extractor=LLMFeatureExtractor(model="stub"),
        generalizer=ContextLikelihoodModel(),
    )


# Load once at module level — avoids repeated sampling (seed=42 → deterministic)
_SCENARIOS, _RESPONSES = load_test_role_dataset(n_responses_per_role=8, seed=42)

ALL_ROLES = {"agent", "target", "observer"}
UNJUST_ACTIONS = {"exploit", "deceive", "coerce", "discriminate"}
JUST_ACTIONS = {"protect", "compensate", "advocate", "assist"}


def _assert_valid_distribution(dist: Dict) -> None:
    assert set(dist.keys()) == {-1, 0, 1}, f"Unexpected keys: {set(dist.keys())}"
    total = sum(dist.values())
    assert abs(total - 1.0) < 1e-6, f"Distribution sums to {total}"
    assert all(0.0 <= v <= 1.0 for v in dist.values())


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def test_dataset_scenario_count():
    assert len(_SCENARIOS) == 100


def test_dataset_response_count():
    # 100 scenarios × 3 roles × 8 responses = 2400
    assert len(_RESPONSES) == 2400


def test_dataset_all_actions_present():
    actions_in_dataset = {s.anchors["action"] for s in _SCENARIOS}
    assert actions_in_dataset == set(action_names())


def test_dataset_scenarios_have_roles():
    for s in _SCENARIOS:
        assert s.roles is not None
        assert "agent" in s.roles
        assert "target" in s.roles


def test_dataset_responses_have_role_perspective():
    for r in _RESPONSES:
        assert r.role_perspective in ALL_ROLES


# ---------------------------------------------------------------------------
# Pipeline: fit
# ---------------------------------------------------------------------------

def test_pipeline_enters_role_mode():
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    assert pipeline._role_mode is True


def test_pipeline_has_all_three_roles_after_fit():
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    assert set(pipeline._role_learners.keys()) == ALL_ROLES
    assert set(pipeline._role_generalizers.keys()) == ALL_ROLES


# ---------------------------------------------------------------------------
# Pipeline: contexts structure
# ---------------------------------------------------------------------------

def test_contexts_returns_role_indexed_dict():
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    assert isinstance(contexts, dict)
    assert set(contexts.keys()) == ALL_ROLES


def test_contexts_each_role_has_valid_structure():
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    for role in ALL_ROLES:
        role_ctx = contexts[role]
        assert isinstance(role_ctx, dict), f"Role '{role}' contexts should be a dict"
        assert len(role_ctx) >= 1, f"Role '{role}' should have at least one action"
        for action, ctx_group in role_ctx.items():
            assert isinstance(action, str)
            for label, entry in ctx_group.items():
                assert "Distribution" in entry, f"Missing 'Distribution' for {role}/{action}/{label}"
                _assert_valid_distribution(entry["Distribution"])


def test_contexts_all_actions_represented():
    """Every action from the dataset should appear in each role's contexts."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()
    expected = set(action_names())

    for role in ALL_ROLES:
        found = set(contexts[role].keys())
        assert expected == found, (
            f"Role '{role}': expected actions {expected}, got {found}"
        )


# ---------------------------------------------------------------------------
# Pipeline: distribution polarity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("action", sorted(UNJUST_ACTIONS))
def test_unjust_action_target_skews_negative(action):
    """Targets should rate clearly unjust actions as Unjust (p(-1) > p(1))."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    target_ctx = contexts["target"].get(action, {})
    assert target_ctx, f"No context for action '{action}' from target perspective"

    dist = list(target_ctx.values())[0]["Distribution"]
    assert dist[-1] > dist[1], (
        f"Target should rate '{action}' as Unjust: p(-1)={dist[-1]:.3f} vs p(1)={dist[1]:.3f}"
    )


@pytest.mark.parametrize("action", sorted(UNJUST_ACTIONS))
def test_unjust_action_observer_skews_negative(action):
    """Observers should rate clearly unjust actions as Unjust (p(-1) > p(1))."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    observer_ctx = contexts["observer"].get(action, {})
    assert observer_ctx, f"No context for action '{action}' from observer perspective"

    dist = list(observer_ctx.values())[0]["Distribution"]
    assert dist[-1] > dist[1], (
        f"Observer should rate '{action}' as Unjust: p(-1)={dist[-1]:.3f} vs p(1)={dist[1]:.3f}"
    )


@pytest.mark.parametrize("action", sorted(UNJUST_ACTIONS))
def test_unjust_action_agent_skews_positive(action):
    """Agents rate their own unjust actions more favourably (p(1) > p(-1))."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    agent_ctx = contexts["agent"].get(action, {})
    assert agent_ctx, f"No context for action '{action}' from agent perspective"

    dist = list(agent_ctx.values())[0]["Distribution"]
    assert dist[1] > dist[-1], (
        f"Agent should rate '{action}' as Just: p(1)={dist[1]:.3f} vs p(-1)={dist[-1]:.3f}"
    )


@pytest.mark.parametrize("action", sorted(JUST_ACTIONS))
@pytest.mark.parametrize("role", sorted(ALL_ROLES))
def test_just_action_skews_positive_all_roles(role, action):
    """All roles should rate clearly just actions as Just (p(1) > p(-1))."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    role_ctx = contexts[role].get(action, {})
    assert role_ctx, f"No context for action '{action}' from {role} perspective"

    dist = list(role_ctx.values())[0]["Distribution"]
    assert dist[1] > dist[-1], (
        f"{role} should rate '{action}' as Just: p(1)={dist[1]:.3f} vs p(-1)={dist[-1]:.3f}"
    )


def test_perspective_divergence_for_exploit():
    """Target should rate exploit as more Unjust than agent (largest divergence in dataset)."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)
    contexts = pipeline.contexts()

    agent_dist = list(contexts["agent"]["exploit"].values())[0]["Distribution"]
    target_dist = list(contexts["target"]["exploit"].values())[0]["Distribution"]

    # Agent rates exploit as more Just than target
    assert agent_dist[1] > target_dist[1], (
        f"Agent should rate exploit as more Just: {agent_dist[1]:.3f} vs {target_dist[1]:.3f}"
    )
    # Target rates exploit as more Unjust than agent
    assert target_dist[-1] > agent_dist[-1], (
        f"Target should rate exploit as more Unjust: {target_dist[-1]:.3f} vs {agent_dist[-1]:.3f}"
    )


# ---------------------------------------------------------------------------
# Pipeline: predict
# ---------------------------------------------------------------------------

def test_predict_returns_valid_distribution_per_role():
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)

    obs = Observation(
        id="obs_test",
        modalities={"text": "An employer withholds wages from a worker."},
        metadata={},
    )
    for role in ALL_ROLES:
        pred = pipeline.predict(obs, role=role)
        assert isinstance(pred, dict), f"predict() for role={role} should return dict"
        assert len(pred) >= 1
        assert abs(sum(pred.values()) - 1.0) < 1e-6, (
            f"Prediction for role={role} sums to {sum(pred.values())}, not 1.0"
        )


def test_predict_without_role_uses_fallback():
    """predict() with no role should not raise in role mode."""
    pipeline = _make_pipeline()
    pipeline.fit(_SCENARIOS, _RESPONSES)

    obs = Observation(
        id="obs_fallback",
        modalities={"text": "Someone holds the door open."},
        metadata={},
    )
    pred = pipeline.predict(obs)
    assert isinstance(pred, dict)
    assert abs(sum(pred.values()) - 1.0) < 1e-6
