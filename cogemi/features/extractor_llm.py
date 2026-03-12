# === 1. Setup ===
import pandas as pd
from sklearn.linear_model import LinearRegression
from typing import Dict, List

from cogemi.observe.scenario import Scenario


class LLMFeatureExtractor:
    '''Extract features from scenarios using a large language model (LLM).
    Example: from the scenario 'A mother lies about Santa Claus to her child.',
    we might extract features like:
    - Comfort-driven: 1, - Low-stakes consequences: 1,
    Preserves emotional well-being: 1,
    Strategic deception: 0, Role-based justification: 0, and so on'''
    def __init__(self, model: str):
        self.model = model  # Placeholder for the actual LLM model
        self.state_distro_dict: Dict = {}  # This will hold the state distributions for each context
        # this prompt is from Marlot et al 2025
        self.action_extraction_prompt = """Prompt: Extract the core action from the scenario and generalize it while preserving key context elements. Retain important qualifiers when necessary but use generic terms. Use a neutral and abstract phrasing in the form: 'To [VERB] [generic object] [optional context]'.
        Examples:
            •	Scenario: A citizen joins a peaceful protest against government corruption despite a law forbidding it.  → To join an illegal protest
            •	Scenario: A protester steals supplies from a corporate warehouse during a riot, even though looting is prohibited. → To steal something during a moment of chaos
            •	Scenario: A lawyer lies to the court about evidence to ensure their client is acquitted. → To lie to protect someone
            •	Scenario: A group organizes a demonstration without permission, risking arrest to voice their concerns. → To organize a protest even though it is illegal
            •	Scenario: A manager decides not to fire underperforming staff to preserve team morale. → To keep unqualified employees instead of replacing them
            •	Scenario: A parent tells their child they did great in a performance to avoid hurting their feelings. → To give false positive feedback to spare someone's feelings
            •	Scenario: A doctor respects a patient's choice to not receive life-saving treatment. → To respect someone's wish to refuse life-saving treatment
            •	Scenario: A researcher tests a new drug on subjects despite risks not being fully known. → To experiment on others despite potential harm
        Now generalize this scenario:
        Scenario:  {dilemma}"""

    def extract_from_scenarios(self, scenarios: List[Scenario]) -> List[List[str]]:
        # Simulate feature extraction by returning dummy features based on context descriptions
        features = []
        for scenario in scenarios:
            features.append(self.extract_from_scenario(scenario))
        return features

    def extract_from_scenario(self, scenario: Scenario) -> List[str]:
        # Placeholder: in a real implementation, this would use the LLM to extract features from the scenario text.
        return ["To do something in a positive way", "To do something in a negative way"]

    def extract_from_context(self, context) -> List[str]:
        # Placeholder: in a real implementation, this would use the LLM to extract features from the context description.
        return ["To do something in a positive way", "To do something in a negative way"]

    @staticmethod
    def distribution(state_label: str) -> Dict[int, float]:
        # Returns a ternary distribution {-1, 0, 1} for a given label
        return {-1: 0.1, 0: 0.2, 1: 0.7} if state_label == 'positive' else {-1: 0.6, 0: 0.3, 1: 0.1}


def extract_action(text: str) -> str:
    # Extracts action from text - this is not part of the
    # LLMFeatureExtractor class - used by TextAbstraction class
    # Placeholder: in a real implementation, this could use
    # an LLM or NLP techniques to identify the main action.
    return "some_action"
