# cogemi/roles/role.py
"""
Role utilities for COGEMI.

A role identifies a participant position within a scenario:
  agent    — the person performing the action
  target   — the person the action is directed at
  observer — a third party witnessing the interaction (optional)

Role perspective is stored in SurveyResponse.role_perspective.
Scenarios with roles carry a `roles` dict, e.g.
  {"agent": "employer", "target": "employee"}
"""

from typing import List, Optional, Set
from cogemi.survey.survey_response import SurveyResponse

VALID_ROLES = ("agent", "target", "observer")


def available_roles(responses: List[SurveyResponse]) -> Set[str]:
    """Return the set of non-None role_perspective values present in responses."""
    return {r.role_perspective for r in responses if r.role_perspective is not None}


def filter_by_role(
    responses: List[SurveyResponse],
    role: str,
) -> List[SurveyResponse]:
    """Return only the responses whose role_perspective matches role."""
    return [r for r in responses if r.role_perspective == role]


def is_role_indexed(responses: List[SurveyResponse]) -> bool:
    """Return True if any response carries a role_perspective."""
    return any(r.role_perspective is not None for r in responses)
