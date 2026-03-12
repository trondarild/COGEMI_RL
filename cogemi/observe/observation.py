from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from .scenario import Scenario

# note what is the difference between this and SurveyResponse in survey_response.py? 
# This is more general, can be used for any kind of observation, not just survey responses. 
# It also has a different structure, with modalities and metadata. 
# We might want to unify these at some point, but for now we can keep them separate.
class Observation:
    """Represents a raw observation with multiple modalities and associated metadata."""
    def __init__(self, id: str, modalities: Dict[str, Any], metadata: Dict[str, Any]):
        self.id = id
        self.modalities = modalities
        self.metadata = metadata


class ObservationAbstraction(ABC):
    @abstractmethod
    def encode_modalities(self, observation: Observation) -> Dict[str, Any]:
        """Encode each modality into a modality-specific latent or token space."""

    @abstractmethod
    def fuse(self, encoded_modalities: Dict[str, Any]) -> Any:
        """Fuse encoded modalities into a single semantic representation."""

    @abstractmethod
    def extract_anchors(self, observation: Observation, representation: Any) -> Dict[str, Any]:
        """Extract slicing anchors (e.g. action, interaction type)."""

    def abstract(self, observation: Observation) -> Scenario:
        """Canonical pipeline: encode → fuse → anchor."""
        encoded = self.encode_modalities(observation)
        fused = self.fuse(encoded)
        anchors = self.extract_anchors(observation, fused)
        return Scenario(id=observation.id, representation=fused, anchors=anchors, origin={})