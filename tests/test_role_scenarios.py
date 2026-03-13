# tests/test_role_scenarios.py
"""
Unit and integration tests for role-indexed COGEMI scenarios.

All LLM calls use model="stub".
"""
import pytest
from typing import Dict, List

from cogemi.api import CogemiPipeline
from cogemi.observe.scenario import Scenario
from cogemi.observe.observation import Observation
from cogemi.survey.survey_response import SurveyResponse
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.roles.role import available_roles, filter_by_role, is_role_indexed
from cogemi.survey.renderer_text import TextSurveyRenderer


JUDGMENT_MAP = {"Unjust": -1, "Neutral": 0, "Just": 1}

ROLE_INSTRUCTIONS = {
    "agent": {
        "en": "You are the agent performing the action. How just is what you are doing?",
        "fr": "Vous êtes l'agent qui effectue l'action. Dans quelle mesure ce que vous faites est-il juste ?"
    },
    "target": {
        "en": "You are the target of the action. How just is what is being done to you?",
        "fr": "Vous êtes la cible de l'action. Dans quelle mesure ce qui vous est fait est-il juste ?"
    },
    "observer": {
        "en": "You are an observer. How just is the agent's action toward the target?",
        "fr": "Vous êtes un observateur. Dans quelle mesure l'action de l'agent envers la cible est-elle juste ?"
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_role_pipeline() -> CogemiPipeline:
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


SCENARIOS = [
    Scenario(
        id="rj_exploit_labor_contract",
        representation="An employer offers a new employee a fixed-rate contract and keeps all profit.",
        anchors={"action": "exploit"},
        roles={"agent": "employer", "target": "employee"},
        origin={},
    ),
    Scenario(
        id="rj_exploit_labor_unpaid",
        representation="A manager asks an intern to work unpaid overtime regularly.",
        anchors={"action": "exploit"},
        roles={"agent": "manager", "target": "intern"},
        origin={},
    ),
    Scenario(
        id="rj_protect_child_hide",
        representation="A parent hides their child from an abusive relative.",
        anchors={"action": "protect"},
        roles={"agent": "parent", "target": "child"},
        origin={},
    ),
    Scenario(
        id="rj_protect_child_lie",
        representation="A parent lies to shield their child from a dangerous stranger.",
        anchors={"action": "protect"},
        roles={"agent": "parent", "target": "child"},
        origin={},
    ),
]


def _make_responses(scenario_id: str, ratings: Dict[str, List[str]]) -> List[SurveyResponse]:
    """ratings: {role: [response, ...]}"""
    out = []
    for role, responses in ratings.items():
        for i, r in enumerate(responses):
            out.append(SurveyResponse(
                participant_id=f"p_{role}_{i}",
                scenario_id=scenario_id,
                response=r,
                role_perspective=role,
            ))
    return out


ALL_RESPONSES = (
    _make_responses("rj_exploit_labor_contract", {
        "agent":    ["Neutral", "Just",   "Just",   "Neutral"],
        "target":   ["Unjust",  "Unjust",  "Unjust",  "Neutral"],
        "observer": ["Unjust",  "Unjust",  "Neutral", "Unjust"],
    }) +
    _make_responses("rj_exploit_labor_unpaid", {
        "agent":    ["Neutral", "Just",   "Neutral", "Just"],
        "target":   ["Unjust",  "Unjust",  "Unjust",  "Unjust"],
        "observer": ["Unjust",  "Neutral", "Unjust",  "Unjust"],
    }) +
    _make_responses("rj_protect_child_hide", {
        "agent":    ["Just",    "Just",    "Just",    "Neutral"],
        "target":   ["Just",    "Just",    "Just",    "Just"],
        "observer": ["Just",    "Just",    "Neutral", "Just"],
    }) +
    _make_responses("rj_protect_child_lie", {
        "agent":    ["Just",    "Just",    "Neutral", "Just"],
        "target":   ["Just",    "Just",    "Just",    "Neutral"],
        "observer": ["Just",    "Neutral", "Just",    "Just"],
    })
)


# ---------------------------------------------------------------------------
# Role utility tests
# ---------------------------------------------------------------------------

def test_is_role_indexed_true():
    responses = [SurveyResponse("p1", "s1", "Just", role_perspective="agent")]
    assert is_role_indexed(responses) is True


def test_is_role_indexed_false():
    responses = [SurveyResponse("p1", "s1", "Just")]
    assert is_role_indexed(responses) is False


def test_available_roles():
    roles = available_roles(ALL_RESPONSES)
    assert roles == {"agent", "target", "observer"}


def test_filter_by_role():
    agent_responses = filter_by_role(ALL_RESPONSES, "agent")
    assert all(r.role_perspective == "agent" for r in agent_responses)
    assert len(agent_responses) > 0


# ---------------------------------------------------------------------------
# Scenario data model tests
# ---------------------------------------------------------------------------

def test_scenario_roles_field():
    s = SCENARIOS[0]
    assert s.roles == {"agent": "employer", "target": "employee"}


def test_scenario_without_roles_is_none():
    s = Scenario(id="s_a_b", representation="text", anchors={}, origin={})
    assert s.roles is None


def test_survey_response_role_perspective():
    r = SurveyResponse("p1", "s1", "Just", role_perspective="target")
    assert r.role_perspective == "target"


def test_survey_response_no_role_is_none():
    r = SurveyResponse("p1", "s1", "Just")
    assert r.role_perspective is None


# ---------------------------------------------------------------------------
# SurveySpecification.instruction_for tests
# ---------------------------------------------------------------------------

def test_instruction_for_role():
    spec = SurveySpecification(
        instructions={"en": "Default question."},
        response_labels=["Unjust", "Neutral", "Just"],
        role_instructions=ROLE_INSTRUCTIONS,
    )
    assert "agent" in spec.instruction_for("agent")
    assert "target" in spec.instruction_for("target")
    assert "observer" in spec.instruction_for("observer")


def test_instruction_for_none_falls_back():
    spec = SurveySpecification(
        instructions={"en": "Default question."},
        response_labels=["Unjust", "Neutral", "Just"],
        role_instructions=ROLE_INSTRUCTIONS,
    )
    assert spec.instruction_for(None) == "Default question."


def test_instruction_for_no_role_instructions():
    spec = SurveySpecification(
        instructions={"en": "Default question."},
        response_labels=["Unjust", "Neutral", "Just"],
    )
    assert spec.instruction_for("agent") == "Default question."


# ---------------------------------------------------------------------------
# TextSurveyRenderer tests
# ---------------------------------------------------------------------------

def test_renderer_uses_role_instruction():
    spec = SurveySpecification(
        instructions={"en": "Default question."},
        response_labels=["Unjust", "Neutral", "Just"],
        role_instructions=ROLE_INSTRUCTIONS,
    )
    renderer = TextSurveyRenderer()
    rendered = renderer.render(SCENARIOS[0], spec, role_perspective="target")
    assert "target" in rendered["question"]
    assert rendered["role_perspective"] == "target"


def test_renderer_no_role_uses_default():
    spec = SurveySpecification(
        instructions={"en": "Default question."},
        response_labels=["Unjust", "Neutral", "Just"],
    )
    renderer = TextSurveyRenderer()
    rendered = renderer.render(SCENARIOS[0], spec)
    assert rendered["question"] == "Default question."
    assert rendered["role_perspective"] is None


# ---------------------------------------------------------------------------
# Pipeline role-mode integration tests
# ---------------------------------------------------------------------------

def test_pipeline_enters_role_mode():
    pipeline = _make_role_pipeline()
    pipeline.fit(SCENARIOS, ALL_RESPONSES)
    assert pipeline._role_mode is True


def test_pipeline_contexts_role_indexed():
    pipeline = _make_role_pipeline()
    pipeline.fit(SCENARIOS, ALL_RESPONSES)
    contexts = pipeline.contexts()

    assert isinstance(contexts, dict)
    assert set(contexts.keys()) == {"agent", "target", "observer"}

    for role, ctx in contexts.items():
        assert isinstance(ctx, dict)
        assert len(ctx) >= 1
        for action, ctx_group in ctx.items():
            for label, entry in ctx_group.items():
                assert "Distribution" in entry
                dist = entry["Distribution"]
                assert set(dist.keys()) == {-1, 0, 1}
                assert abs(sum(dist.values()) - 1.0) < 1e-6


def test_pipeline_role_distributions_differ():
    """Agent should skew positive (Just), target and observer should skew negative (Unjust)
    for the exploitation scenarios."""
    pipeline = _make_role_pipeline()
    pipeline.fit(SCENARIOS, ALL_RESPONSES)
    contexts = pipeline.contexts()

    exploit_agent    = contexts["agent"].get("exploit", {})
    exploit_target   = contexts["target"].get("exploit", {})
    exploit_observer = contexts["observer"].get("exploit", {})

    assert exploit_agent,    "No exploit context for agent"
    assert exploit_target,   "No exploit context for target"
    assert exploit_observer, "No exploit context for observer"

    # Agent rates exploit more favourably than target
    agent_dist  = list(exploit_agent.values())[0]["Distribution"]
    target_dist = list(exploit_target.values())[0]["Distribution"]
    assert agent_dist[1] > target_dist[1], (
        f"Agent should rate exploit as more Just than target: {agent_dist} vs {target_dist}"
    )


def test_pipeline_predict_with_role():
    pipeline = _make_role_pipeline()
    pipeline.fit(SCENARIOS, ALL_RESPONSES)

    obs = Observation(
        id="obs_test",
        modalities={"text": "A landlord charges excessive rent to a vulnerable tenant."},
        metadata={},
    )

    for role in ("agent", "target", "observer"):
        pred = pipeline.predict(obs, role=role)
        assert isinstance(pred, dict)
        assert len(pred) >= 1
        assert abs(sum(pred.values()) - 1.0) < 1e-6, f"Prediction for {role} doesn't sum to 1"


def test_pipeline_non_role_responses_unchanged():
    """A pipeline fitted with non-role responses should behave exactly as before."""
    pipeline = _make_role_pipeline()
    scenarios = [
        Scenario(id="s_cutline_shop", representation="Someone cuts in line.", anchors={}, origin={}),
        Scenario(id="s_holdoor_office", representation="Someone holds the door.", anchors={}, origin={}),
    ]
    responses = [
        SurveyResponse("p1", "s_cutline_shop", "Unjust"),
        SurveyResponse("p2", "s_cutline_shop", "Unjust"),
        SurveyResponse("p3", "s_holdoor_office", "Just"),
        SurveyResponse("p4", "s_holdoor_office", "Just"),
    ]
    pipeline.fit(scenarios, responses)

    assert pipeline._role_mode is False
    contexts = pipeline.contexts()
    assert isinstance(contexts, dict)
    # Should be flat ContextsDict (action → contexts), not role-indexed
    assert "agent" not in contexts
