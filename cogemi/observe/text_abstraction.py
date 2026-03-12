# cogemi/observe/text_abstraction.py
from typing import Any, Dict

from cogemi.observe.observation import ObservationAbstraction
from cogemi.observe.observation import Observation
from cogemi.observe.scenario import Scenario
from cogemi.features.extractor_llm import extract_action # function to extract an "action" anchor from the text, can be a simple keyword extractor or a more complex LLM-based extractor

class TextAbstraction(ObservationAbstraction):
    
    def encode_modalities(self, observation: Observation) -> Dict[str, Any]:
        """Encode each modality into a modality-specific latent or token space."""
        # For text abstraction, we can simply return the raw text modality.
        return {"text": observation.modalities.get("text", "")}
        


    def fuse(self, encoded_modalities: Dict[str, Any]) -> Any:
        """Fuse encoded modalities into a single semantic representation.
        For example, for text abstraction, the fused representation can just be the text itself.
        For more complex abstractions, we could use an LLM to fuse multiple modalities into a
        single representation."""
        # For text abstraction, the fused representation can just be the text itself.
        return encoded_modalities["text"]

    
    def extract_anchors(self, observation: Observation, representation: Any) -> Dict[str, Any]:
        """Extract slicing anchors (e.g. action, interaction type).
        Example: we can extract an "action" anchor from the text using a simple keyword 
        extractor or a more complex LLM-based extractor.
        Or we can extract an interaction type anchor, e.g. 
        "social_interaction", "physical_interaction", etc.
        """
        # For simplicity, we can use a placeholder function to extract an "action" anchor from the text.
        return {"action": extract_action(representation)}

    def abstract(self, observation: Observation) -> Scenario:
        """Canonical pipeline: encode → fuse → anchor."""
        return Scenario(
            id=observation.id,
            representation=observation.modalities["text"], # the text itself of the scenario
            anchors={"action": extract_action(text=observation.modalities["text"])},
            origin={"observation_id": observation.id}
        )
    
    
    
