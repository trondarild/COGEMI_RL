# cogemi/survey/specification.py
from typing import Dict, List, Optional


class SurveySpecification:
    '''
    Example usage:
    appropriateness_spec = SurveySpecification(
        instructions={
            "en": "How socially appropriate is the action in this situation?"
        },
        response_labels=["Inappropriate", "Neutral", "Appropriate"]
    )'''
    def __init__(
        self,
        instructions: Dict[str, str],
        response_labels: List[str],
        language: str = "en",
        metadata_fields: Optional[List[str]] = None
    ):
        self.instructions = instructions
        self.response_labels = response_labels
        self.language = language
        self.metadata_fields: List[str] = metadata_fields or []


class SurveyQuestion:
    """Represents a single survey question, which can be part of a larger SurveySpecification."""
    def __init__(self, id: str, text: str):
        self.id = id
        self.text = text
