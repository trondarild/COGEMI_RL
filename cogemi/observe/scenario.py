from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Scenario:
    """Represents an abstracted scenario with a semantic representation, 
    slicing anchors, and origin information. 
    Explanation of parts:
    id: unique identifier for the scenario
    representation: the abstracted representation of the scenario, e.g. a text description, a graph, a set of features, etc.
    anchors: a dictionary of slicing anchors, e.g. {"action": "cut_in_line", "interaction_type": "social_interaction"}
    origin: a dictionary of provenance information, e.g. {"observation_id": "o1", "abstraction_method": "text_abstraction_v1"}  

    Example usage:
    ```
    scenario = Scenario(
        id="s1",
        representation="Someone cuts in line.",
        anchors={"action": "cut_in_line"},
        origin={"observation_id": "o1"}
    )
    ```
    """
    id: str
    representation: Any
    anchors: Dict[str, Any]
    origin: Dict[str, Any]
