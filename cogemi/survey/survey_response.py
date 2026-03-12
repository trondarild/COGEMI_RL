from typing import Any, Dict, Optional


class SurveyResponse:
    def __init__(
        self,
        participant_id: str,
        scenario_id: str,
        response: str,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.participant_id = participant_id
        self.scenario_id = scenario_id
        self.response = response
        self.response_time = response_time
        self.metadata = metadata   # demographics, role, group, language
