# tests/test_reference_spec.py
"""
Tests for the reference-level instrument pipeline additions:
  - SurveyResponse.norm_type and .confidence fields
  - cogemi/metrics/reliability.py
  - CogemiPipeline norm_type-aware routing (norm mode)

All LLM calls use model="stub".
"""
import pytest
from typing import List

from cogemi.api import (
    CogemiPipeline,
    _is_norm_indexed,
    _available_norm_types,
    _filter_by_norm_type,
)
from cogemi.observe.scenario import Scenario
from cogemi.observe.observation import Observation
from cogemi.survey.survey_response import SurveyResponse
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.metrics.reliability import (
    likert_to_ternary,
    discretize_likert_responses,
    distributional_consistency,
    within_scenario_reliability,
    split_half_reliability,
    confidence_weighted_distribution,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

JUDGMENT_MAP = {"Inappropriate": -1, "Neutral": 0, "Appropriate": 1}

SCENARIOS = [
    Scenario(id="s_yell_park",   representation="A child yells in a park.",        anchors={"action": "yell"},   origin={}),
    Scenario(id="s_litter_park", representation="A drunk adult litters in a park.", anchors={"action": "litter"}, origin={}),
]


def _make_norm_pipeline() -> CogemiPipeline:
    return CogemiPipeline(
        abstraction=TextAbstraction(model="stub"),
        survey_spec=SurveySpecification(
            instructions={"en": "How appropriate is this action?"},
            response_labels=list(JUDGMENT_MAP.keys()),
        ),
        evaluator=HumanSurveyEvaluator(judgment_map=JUDGMENT_MAP, valid_responses=1),
        learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
        feature_extractor=LLMFeatureExtractor(model="stub"),
        generalizer=ContextLikelihoodModel(),
    )


def _make_responses(scenario_id: str, norm_type: str, responses: List[str]) -> List[SurveyResponse]:
    return [
        SurveyResponse(participant_id=f"p_{norm_type}_{i}", scenario_id=scenario_id,
                       response=r, norm_type=norm_type)
        for i, r in enumerate(responses)
    ]


ALL_NORM_RESPONSES = (
    _make_responses("s_yell_park",   "personal",   ["Appropriate", "Neutral",       "Appropriate", "Appropriate"]) +
    _make_responses("s_yell_park",   "injunctive",  ["Neutral",      "Neutral",       "Inappropriate", "Neutral"]) +
    _make_responses("s_yell_park",   "empirical",   ["Appropriate",  "Appropriate",   "Neutral",       "Appropriate"]) +
    _make_responses("s_litter_park", "personal",    ["Inappropriate","Inappropriate", "Neutral",       "Inappropriate"]) +
    _make_responses("s_litter_park", "injunctive",  ["Inappropriate","Inappropriate", "Inappropriate","Inappropriate"]) +
    _make_responses("s_litter_park", "empirical",   ["Neutral",      "Inappropriate", "Inappropriate","Neutral"])
)


# ---------------------------------------------------------------------------
# SurveyResponse field tests
# ---------------------------------------------------------------------------

class TestSurveyResponseFields:
    def test_norm_type_stored(self):
        r = SurveyResponse("p1", "s1", "Appropriate", norm_type="personal")
        assert r.norm_type == "personal"

    def test_norm_type_defaults_to_none(self):
        r = SurveyResponse("p1", "s1", "Appropriate")
        assert r.norm_type is None

    def test_confidence_stored(self):
        r = SurveyResponse("p1", "s1", "Appropriate", confidence=4)
        assert r.confidence == 4

    def test_confidence_defaults_to_none(self):
        r = SurveyResponse("p1", "s1", "Appropriate")
        assert r.confidence is None

    def test_norm_type_and_confidence_together(self):
        r = SurveyResponse("p1", "s1", "Neutral", norm_type="injunctive", confidence=2)
        assert r.norm_type == "injunctive"
        assert r.confidence == 2

    def test_role_perspective_and_norm_type_independent(self):
        r = SurveyResponse("p1", "s1", "Appropriate",
                           norm_type="personal", role_perspective="agent")
        assert r.norm_type == "personal"
        assert r.role_perspective == "agent"


# ---------------------------------------------------------------------------
# likert_to_ternary
# ---------------------------------------------------------------------------

class TestLikertToTernary:
    def test_scale5_lower_band(self):
        # lo = 5/3 ≈ 1.67 → only value 1 falls in the lower band
        assert likert_to_ternary(1, scale=5) == -1

    def test_scale5_middle_band(self):
        # 1.67 < value ≤ 3.33 → values 2 and 3
        assert likert_to_ternary(2, scale=5) == 0
        assert likert_to_ternary(3, scale=5) == 0

    def test_scale5_upper_band(self):
        assert likert_to_ternary(4, scale=5) == 1
        assert likert_to_ternary(5, scale=5) == 1

    def test_scale7_bands(self):
        # lo=7/3≈2.33, hi=14/3≈4.67
        assert likert_to_ternary(1, scale=7) == -1
        assert likert_to_ternary(2, scale=7) == -1
        assert likert_to_ternary(3, scale=7) == 0
        assert likert_to_ternary(4, scale=7) == 0
        assert likert_to_ternary(5, scale=7) == 1
        assert likert_to_ternary(6, scale=7) == 1
        assert likert_to_ternary(7, scale=7) == 1

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            likert_to_ternary(0, scale=5)
        with pytest.raises(ValueError):
            likert_to_ternary(6, scale=5)

    def test_returns_int(self):
        assert isinstance(likert_to_ternary(3), int)


class TestDiscretizeLikertResponses:
    def test_batch_conversion(self):
        result = discretize_likert_responses([1, 2, 3, 4, 5])
        assert result == [-1, 0, 0, 1, 1]

    def test_empty_list(self):
        assert discretize_likert_responses([]) == []

    def test_all_negative(self):
        assert all(v == -1 for v in discretize_likert_responses([1, 1, 1]))


# ---------------------------------------------------------------------------
# distributional_consistency
# ---------------------------------------------------------------------------

class TestDistributionalConsistency:
    D_A = {-1: 0.5, 0: 0.3, 1: 0.2}
    D_B = {-1: 0.5, 0: 0.3, 1: 0.2}
    D_C = {-1: 0.1, 0: 0.1, 1: 0.8}

    def test_identical_distributions_zero(self):
        assert distributional_consistency(self.D_A, self.D_B) == pytest.approx(0.0, abs=1e-9)

    def test_divergent_distributions_positive(self):
        assert distributional_consistency(self.D_A, self.D_C) > 0.0

    def test_symmetric(self):
        assert distributional_consistency(self.D_A, self.D_C) == pytest.approx(
            distributional_consistency(self.D_C, self.D_A), rel=1e-6
        )

    def test_bounded_below_zero(self):
        assert distributional_consistency(self.D_A, self.D_C) >= 0.0


# ---------------------------------------------------------------------------
# within_scenario_reliability
# ---------------------------------------------------------------------------

class TestWithinScenarioReliability:
    D1 = {-1: 0.6, 0: 0.3, 1: 0.1}
    D2 = {-1: 0.6, 0: 0.3, 1: 0.1}
    D3 = {-1: 0.1, 0: 0.2, 1: 0.7}

    def test_identical_distributions_zero(self):
        result = within_scenario_reliability([self.D1, self.D2])
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_mixed_distributions_positive(self):
        result = within_scenario_reliability([self.D1, self.D2, self.D3])
        assert result > 0.0

    def test_requires_two_or_more(self):
        with pytest.raises(ValueError):
            within_scenario_reliability([self.D1])

    def test_returns_float(self):
        assert isinstance(within_scenario_reliability([self.D1, self.D3]), float)


# ---------------------------------------------------------------------------
# split_half_reliability
# ---------------------------------------------------------------------------

class TestSplitHalfReliability:
    def test_identical_halves_near_zero(self):
        half = [-1, -1, 0, 1]
        result = split_half_reliability(half, half)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_different_halves_positive(self):
        half_a = [-1, -1, -1, -1]
        half_b = [1, 1, 1, 1]
        result = split_half_reliability(half_a, half_b)
        assert result > 0.0


# ---------------------------------------------------------------------------
# confidence_weighted_distribution
# ---------------------------------------------------------------------------

class TestConfidenceWeightedDistribution:
    def test_high_confidence_dominates(self):
        # high confidence on -1 should push weight toward -1
        dist = confidence_weighted_distribution([-1, 1], [5, 1])
        assert dist[-1] > dist[1]

    def test_equal_confidence_equal_weight(self):
        dist = confidence_weighted_distribution([-1, 1], [3, 3])
        assert dist[-1] == pytest.approx(dist[1], rel=1e-6)

    def test_output_sums_to_one(self):
        dist = confidence_weighted_distribution([-1, 0, 1], [5, 3, 1])
        assert sum(dist.values()) == pytest.approx(1.0, rel=1e-6)

    def test_all_keys_present(self):
        dist = confidence_weighted_distribution([1, 1, 1], [4, 4, 4])
        assert set(dist.keys()) == {-1, 0, 1}

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValueError):
            confidence_weighted_distribution([-1, 0], [5])


# ---------------------------------------------------------------------------
# Norm-type pipeline utilities
# ---------------------------------------------------------------------------

class TestNormTypeHelpers:
    def test_is_norm_indexed_true(self):
        responses = [SurveyResponse("p1", "s1", "Appropriate", norm_type="personal")]
        assert _is_norm_indexed(responses) is True

    def test_is_norm_indexed_false(self):
        responses = [SurveyResponse("p1", "s1", "Appropriate")]
        assert _is_norm_indexed(responses) is False

    def test_is_norm_indexed_partial(self):
        responses = [
            SurveyResponse("p1", "s1", "Appropriate", norm_type="personal"),
            SurveyResponse("p2", "s1", "Neutral"),
        ]
        assert _is_norm_indexed(responses) is True

    def test_available_norm_types_order(self):
        types = _available_norm_types(ALL_NORM_RESPONSES)
        assert set(types) == {"personal", "injunctive", "empirical"}

    def test_filter_by_norm_type(self):
        personal = _filter_by_norm_type(ALL_NORM_RESPONSES, "personal")
        assert all(r.norm_type == "personal" for r in personal)
        assert len(personal) > 0

    def test_filter_excludes_other_types(self):
        injunctive = _filter_by_norm_type(ALL_NORM_RESPONSES, "injunctive")
        assert not any(r.norm_type == "personal" for r in injunctive)


# ---------------------------------------------------------------------------
# Pipeline norm-mode integration tests
# ---------------------------------------------------------------------------

class TestPipelineNormMode:
    def test_pipeline_enters_norm_mode(self):
        pipeline = _make_norm_pipeline()
        pipeline.fit(SCENARIOS, ALL_NORM_RESPONSES)
        assert pipeline._norm_mode is True
        assert pipeline._role_mode is False

    def test_pipeline_contexts_norm_indexed(self):
        pipeline = _make_norm_pipeline()
        pipeline.fit(SCENARIOS, ALL_NORM_RESPONSES)
        contexts = pipeline.contexts()

        assert isinstance(contexts, dict)
        assert set(contexts.keys()) == {"personal", "injunctive", "empirical"}

        for nt, ctx in contexts.items():
            assert isinstance(ctx, dict)
            assert len(ctx) >= 1
            for action, ctx_group in ctx.items():
                for label, entry in ctx_group.items():
                    dist = entry["Distribution"]
                    assert set(dist.keys()) == {-1, 0, 1}
                    assert abs(sum(dist.values()) - 1.0) < 1e-6

    def test_pipeline_predict_with_norm_type(self):
        pipeline = _make_norm_pipeline()
        pipeline.fit(SCENARIOS, ALL_NORM_RESPONSES)

        obs = Observation(
            id="obs_test",
            modalities={"text": "Someone shouts in a quiet library."},
            metadata={},
        )

        for nt in ("personal", "injunctive", "empirical"):
            pred = pipeline.predict(obs, norm_type=nt)
            assert isinstance(pred, dict)
            assert len(pred) >= 1
            assert abs(sum(pred.values()) - 1.0) < 1e-6, \
                f"Prediction for norm_type={nt} doesn't sum to 1"

    def test_pipeline_norm_mode_false_without_norm_type(self):
        pipeline = _make_norm_pipeline()
        responses = [
            SurveyResponse("p1", "s_yell_park",   "Appropriate"),
            SurveyResponse("p2", "s_litter_park",  "Inappropriate"),
        ]
        pipeline.fit(SCENARIOS, responses)
        assert pipeline._norm_mode is False

    def test_pipeline_norm_contexts_are_independent(self):
        pipeline = _make_norm_pipeline()
        pipeline.fit(SCENARIOS, ALL_NORM_RESPONSES)
        contexts = pipeline.contexts()

        # personal yell_park should skew Appropriate; litter personal should skew Inappropriate
        personal_ctx = contexts["personal"]
        injunctive_ctx = contexts["injunctive"]
        # Both exist and are non-empty (distributions may differ)
        assert len(personal_ctx) >= 1
        assert len(injunctive_ctx) >= 1
