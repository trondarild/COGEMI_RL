# cogemi/features/extractor_llm.py
import re
from typing import Dict, List, Optional

import ollama

from cogemi.observe.scenario import Scenario

DEFAULT_MODEL = "qwen3:1.7b"

# Prompt from Marlot et al. 2025 — extracts a generalised action label from a scenario
_ACTION_EXTRACTION_PROMPT = """\
Extract the core action from the scenario and generalize it while preserving \
key context elements. Retain important qualifiers when necessary but use generic \
terms. Use a neutral and abstract phrasing in the form: \
'To [VERB] [generic object] [optional context]'.

Examples:
  Scenario: A citizen joins a peaceful protest against government corruption \
despite a law forbidding it.
  → To join an illegal protest

  Scenario: A protester steals supplies from a corporate warehouse during a \
riot, even though looting is prohibited.
  → To steal something during a moment of chaos

  Scenario: A lawyer lies to the court about evidence to ensure their client \
is acquitted.
  → To lie to protect someone

  Scenario: A parent tells their child they did great in a performance to avoid \
hurting their feelings.
  → To give false positive feedback to spare someone's feelings

  Scenario: A doctor respects a patient's choice to not receive life-saving \
treatment.
  → To respect someone's wish to refuse life-saving treatment

Now generalize this scenario. Reply with ONLY the generalized action, \
no explanation:
Scenario: {scenario}"""

# Prompt for extracting a short list of semantic feature labels from a scenario
_FEATURE_EXTRACTION_PROMPT = """\
Given the scenario below, list 2–4 short phrases that capture its morally \
relevant features — i.e. the kinds of considerations a person would weigh when \
judging whether the action is appropriate or just.

Each phrase should start with a gerund or noun (e.g. "Protective intent", \
"Deception for personal gain", "Respect for autonomy").

Reply with ONLY a comma-separated list of phrases, no numbering, \
no explanation.

Scenario: {scenario}"""


class LLMFeatureExtractor:
    """Extract features from scenarios using a large language model.

    Pass model="stub" to skip LLM calls and return hardcoded responses —
    useful for unit tests and pipeline smoke tests.

    Pass any Ollama model name (e.g. "qwen3:1.7b") for real extraction.
    """

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_scenarios(self, scenarios: List[Scenario]) -> List[List[str]]:
        """Extract feature labels for each scenario in the list."""
        return [self.extract_from_scenario(s) for s in scenarios]

    def extract_from_scenario(self, scenario: Scenario) -> List[str]:
        """Return a list of semantic feature labels for a single scenario."""
        if self.model == "stub":
            return ["To do something in a positive way", "To do something in a negative way"]
        raw = self._call(
            _FEATURE_EXTRACTION_PROMPT.format(scenario=scenario.representation)
        )
        return _parse_csv_list(raw)

    def extract_from_context(self, context: Dict) -> List[str]:
        """Return feature labels summarising a context entry."""
        if self.model == "stub":
            return ["To do something in a positive way", "To do something in a negative way"]
        # Build a short description from states stored in the context
        states = context.get("States", [])
        state_texts = ", ".join(str(s[0]) for s in states[:5])
        description = f"A context with states: {state_texts}"
        raw = self._call(
            _FEATURE_EXTRACTION_PROMPT.format(scenario=description)
        )
        return _parse_csv_list(raw)

    def extract_action(self, text: str) -> str:
        """Extract a single generalised action label from free text."""
        if self.model == "stub":
            return "To do something"
        raw = self._call(
            _ACTION_EXTRACTION_PROMPT.format(scenario=text)
        )
        return raw.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the response text."""
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
        )
        return response.message.content.strip()

    @staticmethod
    def distribution(state_label: str) -> Dict[int, float]:
        """Return a ternary distribution for a named state label (utility method)."""
        return (
            {-1: 0.1, 0: 0.2, 1: 0.7}
            if state_label == "positive"
            else {-1: 0.6, 0: 0.3, 1: 0.1}
        )


# ---------------------------------------------------------------------------
# Module-level helper used by TextAbstraction
# ---------------------------------------------------------------------------

def extract_action(text: str, model: str = DEFAULT_MODEL) -> str:
    """Extract a generalised action label from scenario text.

    Uses the LLMFeatureExtractor with the given model.
    Pass model="stub" for tests.
    """
    return LLMFeatureExtractor(model=model).extract_action(text)


# ---------------------------------------------------------------------------
# Internal parsing helper
# ---------------------------------------------------------------------------

def _parse_csv_list(raw: str) -> List[str]:
    """Parse a comma-separated LLM response into a clean list of strings.

    Strips whitespace, quotes, and empty entries. Falls back to the whole
    string as a single item if no commas are found.
    """
    # Strip common thinking-model tags (e.g. <think>...</think>)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    items = [item.strip().strip('"').strip("'") for item in raw.split(",")]
    items = [item for item in items if item]
    return items if items else [raw.strip()]
