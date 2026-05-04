# cogemi/api.py
from typing import Dict, List, Any, Optional, Union

from cogemi.observe.observation import Observation
from cogemi.observe.scenario import Scenario
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.survey.survey_renderer import SurveyRenderer
from cogemi.survey.specification import SurveySpecification, SurveyQuestion
from cogemi.survey.survey_response import SurveyResponse
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner, ContextsDict
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.roles.role import available_roles, filter_by_role, is_role_indexed
from cogemi.metrics.reliability import (
    likert_to_ternary,
    discretize_likert_responses,
    confidence_weighted_distribution,
)


NORM_TYPES = ("personal", "injunctive", "empirical")


def _is_norm_indexed(responses: List[SurveyResponse]) -> bool:
    return any(r.norm_type is not None for r in responses)


def _available_norm_types(responses: List[SurveyResponse]) -> List[str]:
    seen: List[str] = []
    for r in responses:
        if r.norm_type and r.norm_type not in seen:
            seen.append(r.norm_type)
    return seen


def _filter_by_norm_type(responses: List[SurveyResponse], norm_type: str) -> List[SurveyResponse]:
    return [r for r in responses if r.norm_type == norm_type]


class CogemiPipeline:
    def __init__(
        self,
        abstraction: TextAbstraction,
        survey_spec: SurveySpecification,
        evaluator: HumanSurveyEvaluator,
        learner: ContextLearner,
        feature_extractor: LLMFeatureExtractor,
        generalizer: ContextLikelihoodModel
    ):
        self.abstraction = abstraction
        self.survey_spec = survey_spec
        self.evaluator = evaluator
        self.learner = learner
        self.feature_extractor = feature_extractor
        self.generalizer = generalizer

        # Set after fit() when responses carry role_perspective values
        self._role_mode: bool = False
        self._role_learners: Dict[str, ContextLearner] = {}
        self._role_generalizers: Dict[str, ContextLikelihoodModel] = {}

        # Set after fit() when responses carry norm_type values
        self._norm_mode: bool = False
        self._norm_learners: Dict[str, ContextLearner] = {}
        self._norm_generalizers: Dict[str, ContextLikelihoodModel] = {}

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def simple_appropriateness_pipeline() -> "CogemiPipeline":
        return CogemiPipeline(
            abstraction=TextAbstraction(),
            survey_spec=SurveySpecification(
                instructions={"en": "How socially appropriate is the action in this situation?"},
                response_labels=["Inappropriate", "Neutral", "Appropriate"]
            ),
            evaluator=HumanSurveyEvaluator(judgment_map={"Inappropriate": -1, "Neutral": 0, "Appropriate": 1}, valid_responses=30),
            learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
            feature_extractor=LLMFeatureExtractor(model="stub"),
            generalizer=ContextLikelihoodModel()
        )

    @staticmethod
    def simple_justice_pipeline() -> "CogemiPipeline":
        return CogemiPipeline(
            abstraction=TextAbstraction(),
            survey_spec=SurveySpecification(
                instructions={"en": "How just is the action in this situation?"},
                response_labels=["Unjust", "Neutral", "Just"]
            ),
            evaluator=HumanSurveyEvaluator(judgment_map={"Unjust": -1, "Neutral": 0, "Just": 1}, valid_responses=30),
            learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
            feature_extractor=LLMFeatureExtractor(model="stub"),
            generalizer=ContextLikelihoodModel()
        )

    @staticmethod
    def simple_effort_pipeline() -> "CogemiPipeline":
        return CogemiPipeline(
            abstraction=TextAbstraction(),
            survey_spec=SurveySpecification(
                instructions={"en": "How much effort does the action in this situation require?"},
                response_labels=["Low Effort", "Neutral", "High Effort"]
            ),
            evaluator=HumanSurveyEvaluator(judgment_map={"Low Effort": -1, "Neutral": 0, "High Effort": 1}, valid_responses=30),
            learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
            feature_extractor=LLMFeatureExtractor(model="stub"),
            generalizer=ContextLikelihoodModel()
        )

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def fit(self, scenarios: List[Scenario], survey_responses: List[SurveyResponse]) -> None:
        """Fit the pipeline with the given scenarios and survey responses.

        When survey_responses carry role_perspective values the pipeline
        automatically enters role mode: one sub-pipeline is fitted per role.

        When survey_responses carry norm_type values ("personal", "injunctive",
        "empirical") the pipeline enters norm mode: one sub-pipeline is fitted
        per norm type.  Role mode and norm mode are mutually exclusive; role
        mode takes precedence when both fields are set.

        Responses without a role_perspective / norm_type are handled in the
        standard (non-role, non-norm) path.
        """
        if is_role_indexed(survey_responses):
            self._role_mode = True
            self._norm_mode = False
            self._role_learners = {}
            self._role_generalizers = {}
            for role in available_roles(survey_responses):
                role_responses = filter_by_role(survey_responses, role)
                learner, generalizer = self._fit_single(scenarios, role_responses)
                self._role_learners[role] = learner
                self._role_generalizers[role] = generalizer
        elif _is_norm_indexed(survey_responses):
            self._norm_mode = True
            self._role_mode = False
            self._norm_learners = {}
            self._norm_generalizers = {}
            for norm_type in _available_norm_types(survey_responses):
                typed_responses = _filter_by_norm_type(survey_responses, norm_type)
                learner, generalizer = self._fit_single(scenarios, typed_responses)
                self._norm_learners[norm_type] = learner
                self._norm_generalizers[norm_type] = generalizer
        else:
            self._role_mode = False
            self._norm_mode = False
            samples = self.map_responses_to_samples(survey_responses)
            contexts = self.learner.fit(scenarios, samples)
            features = [self.feature_extractor.extract_from_scenario(s) for s in scenarios]
            self.generalizer.fit(features, contexts)

    def _fit_single(
        self,
        scenarios: List[Scenario],
        responses: List[SurveyResponse],
    ) -> tuple:
        """Fit a fresh ContextLearner + ContextLikelihoodModel for one subset of responses.

        Only scenarios that have at least one response are included, ordered
        by first occurrence in the response list.
        """
        scenario_map = {s.id: s for s in scenarios}
        seen: List[str] = []
        for r in responses:
            if r.scenario_id in scenario_map and r.scenario_id not in seen:
                seen.append(r.scenario_id)
        ordered_scenarios = [scenario_map[sid] for sid in seen]

        samples = self.map_responses_to_samples(responses)

        learner = ContextLearner(
            add_threshold=self.learner.add_threshold,
            merge_threshold=self.learner.merge_threshold,
            metric=self.learner.metric,
        )
        generalizer = ContextLikelihoodModel()

        context_labels = learner.fit(ordered_scenarios, samples)
        features = [self.feature_extractor.extract_from_scenario(s) for s in ordered_scenarios]
        generalizer.fit(features, context_labels)

        return learner, generalizer

    def map_responses_to_samples(self, survey_responses: List[SurveyResponse]) -> List[List[float]]:
        """Map survey responses to per-scenario lists of numerical samples."""
        samples: Dict[str, List[float]] = {}
        for response in survey_responses:
            scenario_id = response.scenario_id
            if scenario_id not in samples:
                samples[scenario_id] = []
            mapped_value = self.evaluator.judgment_map.get(response.response, 0)
            samples[scenario_id].append(mapped_value)
        return list(samples.values())

    def contexts(self) -> Union[ContextsDict, Dict[str, ContextsDict]]:
        """Return learned contexts.

        In role mode returns {role: ContextsDict}.
        In norm mode returns {norm_type: ContextsDict}.
        In standard mode returns ContextsDict.
        """
        if self._role_mode:
            return {role: learner.contexts() for role, learner in self._role_learners.items()}
        if self._norm_mode:
            return {nt: learner.contexts() for nt, learner in self._norm_learners.items()}
        return self.learner.contexts()

    def predict(
        self,
        new_observation: Observation,
        role: Optional[str] = None,
        norm_type: Optional[str] = None,
    ) -> Dict[str, float]:
        """Predict the context probability distribution for a new observation.

        In role mode, supply role="agent"/"target"/"observer".
        In norm mode, supply norm_type="personal"/"injunctive"/"empirical".
        Falls back to the first fitted sub-pipeline if the key is not found.
        """
        abstracted = self.abstraction.abstract(new_observation)
        features = self.feature_extractor.extract_from_scenario(abstracted)

        if self._role_mode:
            if role and role in self._role_generalizers:
                return self._role_generalizers[role].predict_proba(features)
            fallback = next(iter(self._role_generalizers.values()), self.generalizer)
            return fallback.predict_proba(features)

        if self._norm_mode:
            if norm_type and norm_type in self._norm_generalizers:
                return self._norm_generalizers[norm_type].predict_proba(features)
            fallback = next(iter(self._norm_generalizers.values()), self.generalizer)
            return fallback.predict_proba(features)

        return self.generalizer.predict_proba(features)
