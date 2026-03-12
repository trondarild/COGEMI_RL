# cogemi/api.py
from typing import Dict, List, Any

from cogemi.observe.observation import Observation
from cogemi.observe.scenario import Scenario
from cogemi.observe.text_abstraction import TextAbstraction
from cogemi.survey.survey_renderer import SurveyRenderer
from cogemi.survey.specification import SurveySpecification, SurveyQuestion
from cogemi.survey.survey_response import SurveyResponse
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel


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
        """Initialize the pipeline with the given components."""
        self.abstraction = abstraction
        self.survey_spec = survey_spec
        self.evaluator = evaluator
        self.learner = learner
        self.feature_extractor = feature_extractor
        self.generalizer = generalizer

    @staticmethod
    def simple_appropriateness_pipeline() -> "CogemiPipeline":
        """Return a simple appropriateness pipeline configuration."""
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
        """Return a simple justice pipeline configuration."""
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
        """Return a simple effort pipeline configuration."""
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

    def fit(self, scenarios: List[Scenario], survey_responses: List[SurveyResponse]) -> None:
        """Fit the pipeline with the given scenarios and survey responses."""
        # Step 1: Abstract the scenarios (not needed when given scenarios directly)
        # abstracted = [self.abstraction.abstract(scenario) for scenario in scenarios]

        # Map survey responses to per-scenario numerical sample lists
        samples = self.map_responses_to_samples(survey_responses)

        # Step 2: Fit the context learner; returns list of learned contexts
        contexts = self.learner.fit(scenarios, samples)

        # Step 3: Extract features from the scenarios
        features = [self.feature_extractor.extract_from_scenario(scenario) for scenario in scenarios]

        # Step 4: Fit the generalizer with features → contexts
        self.generalizer.fit(features, contexts)

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

    def contexts(self) -> list:
        """Return the contexts learned by the pipeline."""
        return self.learner.contexts()

    def predict(self, new_observation: Observation) -> Dict[str, float]:
        """Predict the reward distribution for a new observation."""
        abstracted = self.abstraction.abstract(new_observation)
        features = self.feature_extractor.extract_from_scenario(abstracted)
        return self.generalizer.predict_proba(features)
