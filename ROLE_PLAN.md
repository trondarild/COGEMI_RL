# Role Support Plan for COGEMI

## What role support means

A **role** is a participant position within a scenario. Scenarios currently have a single implicit perspective ("someone does X"). Role support makes the participant positions explicit and allows survey questions and evaluation distributions to be indexed by those positions.

### The three roles

| Role | Meaning | Example |
|---|---|---|
| `agent` | The person performing the action | Employer offering a contract |
| `target` | The person the action is directed at | Employee receiving the offer |
| `observer` | A third party witnessing the interaction | Bystander watching the exchange |

`agent` and `target` are always present in a role-scenario. `observer` is optional.

### What role support enables

For the same scenario, a survey participant can be assigned one of the following question framings:

| Dimension | Agent framing | Target framing | Observer framing |
|---|---|---|---|
| Justice | "Is what you are doing just?" | "Is what is being done to you just?" | "Is what the agent is doing to the target just?" |
| Appropriateness | "Is your action socially appropriate?" | "Is the action directed at you appropriate?" | "Is the agent's action toward the target appropriate?" |
| Effort/cost | "Is this action costly or effortful for you?" | "Is this situation costly or effortful for you?" | — |

### Representative scenarios

```
Agent: an employer
Target: a new employee
Action: offering a fixed-rate contract and taking all profit

Agent framing (justice): "You are an employer offering a fixed-rate contract and keeping all profit. Is this just?"
Target framing (justice): "You are a new employee offered a fixed-rate contract while your employer takes all profit. Is this just?"
Observer framing (justice): "An employer offers a new employee a fixed-rate contract and keeps all profit. Is this just?"
```

The three responses to this scenario may produce very different distributions — a core empirical question that role support makes measurable.

---

## Data model changes

### `Scenario` — add `roles` field

```python
@dataclass
class Scenario:
    id: str
    representation: Any
    anchors: Dict[str, Any]
    origin: Dict[str, Any]
    roles: Optional[Dict[str, str]] = None  # NEW
    # e.g. {"agent": "employer", "target": "employee"}
```

`roles` is `None` for all existing (non-role) scenarios — fully backward compatible.

### `SurveyResponse` — add `role_perspective` field

```python
class SurveyResponse:
    def __init__(self, ..., role_perspective: Optional[str] = None):
        ...
        self.role_perspective = role_perspective   # NEW: "agent" | "target" | "observer" | None
```

`None` means the response has no role perspective (existing data unaffected).

### `SurveySpecification` — add `role_instructions`

```python
class SurveySpecification:
    def __init__(self, ..., role_instructions: Optional[Dict[str, Dict[str, str]]] = None):
        ...
        self.role_instructions = role_instructions   # NEW
        # Structure: {role: {lang: instruction_text}}
        # e.g. {
        #   "agent":    {"en": "As the agent, ...", "fr": "En tant qu'agent, ..."},
        #   "target":   {"en": "As the target, ...", "fr": "En tant que cible, ..."},
        #   "observer": {"en": "As an observer, ...", "fr": "En tant qu'observateur, ..."},
        # }
```

Falls back to `instructions` when no role perspective is specified.

---

## Pipeline behaviour with roles

The pipeline runs **one sub-pipeline per role perspective**. Each role's responses are evaluated and fitted independently, yielding role-indexed context distributions.

```
survey_responses (with role_perspective set)
    │
    ├─ filter role="agent"    → fit sub-pipeline A → contexts_agent
    ├─ filter role="target"   → fit sub-pipeline B → contexts_target
    └─ filter role="observer" → fit sub-pipeline C → contexts_observer
```

`contexts()` returns `{role: ContextsDict}`.
`predict(obs, role=...)` returns the distribution for that role's generalizer.

When all `role_perspective` values are `None` (i.e. legacy data), the pipeline runs exactly as before and `contexts()` returns the existing flat `ContextsDict`.

### `CogemiPipeline` changes

- `fit()`: detect whether responses carry `role_perspective`; if so, partition and fit per role, storing `{role: learner}` and `{role: generalizer}` dicts internally
- `contexts()`: return `{role: ContextsDict}` if role-indexed, else `ContextsDict` as now
- `predict(obs, role=None)`: use the role-specific generalizer if role given, else default

---

## New module: `cogemi/roles/role.py`

```python
VALID_ROLES = ("agent", "target", "observer")

def filter_by_role(responses, role):
    """Return only SurveyResponses whose role_perspective matches role."""

def available_roles(responses):
    """Return the set of role_perspective values present in responses."""
```

---

## File change map

| File | Type | Change |
|---|---|---|
| `cogemi/observe/scenario.py` | Data model | Add `roles: Optional[Dict[str, str]] = None` |
| `cogemi/survey/survey_response.py` | Data model | Add `role_perspective: Optional[str] = None` |
| `cogemi/survey/specification.py` | Data model | Add `role_instructions: Optional[Dict[str, Dict[str, str]]] = None` |
| `cogemi/survey/renderer_text.py` | Renderer | Use `role_instructions[role_perspective][lang]` when available |
| `cogemi/roles/role.py` | New file | `VALID_ROLES`, `filter_by_role()`, `available_roles()` |
| `cogemi/api.py` | Pipeline | Role-aware `fit()`, `contexts()`, `predict()` |
| `tests/test_role_scenarios.py` | New test | Unit + integration tests for role-indexed pipeline |

No existing tests or callers need to change — all new fields default to `None`.

---

## Example usage (target state)

```python
from cogemi.api import CogemiPipeline
from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

scenario = Scenario(
    id="rj_exploit_labor_contract",
    representation="An employer offers a new employee a fixed-rate contract and keeps all profit.",
    anchors={"action": "exploit_labor"},
    roles={"agent": "employer", "target": "employee"},
    origin={}
)

responses = [
    SurveyResponse("p1", scenario.id, "Unjust",   role_perspective="target"),
    SurveyResponse("p2", scenario.id, "Just",     role_perspective="agent"),
    SurveyResponse("p3", scenario.id, "Unjust",   role_perspective="observer"),
]

pipeline = CogemiPipeline.simple_justice_pipeline()
pipeline.fit([scenario], responses)

contexts = pipeline.contexts()
# {"target": {"exploit_labor": {"C1": {...}}},
#  "agent":  {"exploit_labor": {"C1": {...}}},
#  "observer": {...}}

pred = pipeline.predict(new_observation, role="target")
```

---

## Scenario ID convention for role scenarios

Extend the existing `prefix_action_state` convention:

```
rj_{action}_{state}    — role-justice scenarios
ra_{action}_{state}    — role-appropriateness scenarios
re_{action}_{state}    — role-effort scenarios
```

`ContextLearner` still extracts `action` (index 1) and `state` (index 2) from the ID — the prefix just signals that roles are in play.
