# evaluation/response.py
# A more structured survey response that inherits Observation.
# Named EvaluationSurveyResponse to avoid collision with survey.survey_response.SurveyResponse.
from typing import Any, Dict, Optional

from cogemi.observe.observation import Observation


class EvaluationSurveyResponse(Observation):
    def __init__(
        self,
        participant_id: str,
        scenario_id: str,
        response_label: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(id=scenario_id, modalities={}, metadata=metadata or {})
        self.participant_id = participant_id
        self.scenario_id = scenario_id
        self.response_label = response_label
        self.timestamp = timestamp
