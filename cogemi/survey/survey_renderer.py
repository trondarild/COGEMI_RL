from abc import ABC, abstractmethod
from typing import Any

from cogemi.observe.scenario import Scenario
from cogemi.survey.specification import SurveySpecification


class SurveyRenderer(ABC):
    """
    Abstract base class for rendering survey items based on a scenario and survey specification.
    """

    @abstractmethod
    def render(
        self,
        scenario: Scenario,
        survey_spec: SurveySpecification,
        language: str
    ) -> Any:
        """
        Produce a human-facing item:
        text, HTML fragment, multimodal stimulus, etc.
        """
