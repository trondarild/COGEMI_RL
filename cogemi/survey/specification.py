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
        metadata_fields: Optional[List[str]] = None,
        role_instructions: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        self.instructions = instructions
        self.response_labels = response_labels
        self.language = language
        self.metadata_fields: List[str] = metadata_fields or []
        # role_instructions: {role: {lang: question_text}}
        # e.g. {"agent": {"en": "As the agent, how just is this?", "fr": "..."}}
        # Falls back to self.instructions when role_perspective is None.
        self.role_instructions: Optional[Dict[str, Dict[str, str]]] = role_instructions

    def instruction_for(self, role_perspective: Optional[str] = None) -> str:
        """Return the instruction string for the given role and current language."""
        if role_perspective and self.role_instructions:
            role_map = self.role_instructions.get(role_perspective, {})
            if self.language in role_map:
                return role_map[self.language]
        return self.instructions.get(self.language, "")


class SurveyQuestion:
    """Represents a single survey question, which can be part of a larger SurveySpecification."""
    def __init__(self, id: str, text: str):
        self.id = id
        self.text = text
