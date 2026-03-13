from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Scenario:
    """Represents an abstracted scenario with a semantic representation,
    slicing anchors, and origin information.

    Fields:
    - id: unique identifier in format "prefix_action_state" (e.g. "s_cutline_supermarket")
    - representation: text or other description of the scenario
    - anchors: slicing anchors, e.g. {"action": "cut_in_line"}
    - origin: provenance, e.g. {"observation_id": "o1"}
    - roles: optional participant roles, e.g. {"agent": "employer", "target": "employee"}.
             None for scenarios without explicit roles (backward compatible).
    """
    id: str
    representation: Any
    anchors: Dict[str, Any]
    origin: Dict[str, Any]
    roles: Optional[Dict[str, str]] = field(default=None)
