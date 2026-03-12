# cogemi/observe/text_abstraction.py
from typing import Any, Dict

from cogemi.observe.observation import ObservationAbstraction, Observation
from cogemi.observe.scenario import Scenario
from cogemi.features.extractor_llm import extract_action, DEFAULT_MODEL


class TextAbstraction(ObservationAbstraction):

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def encode_modalities(self, observation: Observation) -> Dict[str, Any]:
        """Encode each modality into a modality-specific latent or token space."""
        return {"text": observation.modalities.get("text", "")}

    def fuse(self, encoded_modalities: Dict[str, Any]) -> Any:
        """Fuse encoded modalities into a single semantic representation."""
        return encoded_modalities["text"]

    def extract_anchors(self, observation: Observation, representation: Any) -> Dict[str, Any]:
        """Extract slicing anchors (e.g. action type) from the fused representation."""
        return {"action": extract_action(text=representation, model=self.model)}

    def abstract(self, observation: Observation) -> Scenario:
        """Canonical pipeline: encode → fuse → anchor."""
        text = observation.modalities["text"]
        return Scenario(
            id=observation.id,
            representation=text,
            anchors={"action": extract_action(text=text, model=self.model)},
            origin={"observation_id": observation.id}
        )
