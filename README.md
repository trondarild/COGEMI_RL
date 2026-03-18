# COGEMI_RL
Contextual Organization of General Evaluation from Multimodal Inputs

A library for learning contextual, situational valence from human survey data.

Based on [COMETH_RL](link).

---

## Pipeline overview

```mermaid
flowchart TD
    OBS["<b>Observation</b><br/>id: str<br/>modalities: Dict[str, Any]<br/>metadata: Dict[str, Any]"]
    ABS["<b>TextAbstraction</b><br/>.abstract(observation)"]
    SCN["<b>Scenario</b><br/>id: str<br/>representation: Any<br/>anchors: Dict[str, Any]<br/>origin: Dict[str, Any]"]
    SRV["<b>SurveyResponse</b><br/>participant_id: str<br/>scenario_id: str<br/>response: str<br/>role_perspective: str | None"]
    MAP["<b>map_responses_to_samples()</b><br/>judgment_map: Dict[str, float]"]
    SAM["<b>samples</b><br/>List[List[float]]<br/>e.g. [[-1,-1,0,1], [0,1,1]]"]
    CL["<b>ContextLearner</b><br/>.fit(scenarios, samples)<br/>add_threshold: float<br/>merge_threshold: float"]
    CTX["<b>context labels</b><br/>List[str]<br/>e.g. ['cut_in_line:C1', 'cut_in_line:C2']"]
    FE["<b>LLMFeatureExtractor</b><br/>.extract_from_scenario(scenario)"]
    FEAT["<b>features</b><br/>List[List[str]]<br/>e.g. [['To do X', 'To do Y'], ...]"]
    GEN["<b>ContextLikelihoodModel</b><br/>.fit(features, context_labels)<br/>.predict_proba(features)"]
    PRED["<b>prediction</b><br/>Dict[str, float]<br/>context → probability"]

    OBS --> ABS --> SCN
    SCN --> FE --> FEAT
    SRV --> MAP --> SAM
    SCN --> CL
    SAM --> CL --> CTX
    FEAT --> GEN
    CTX --> GEN
    GEN --> PRED
```

### Training path
1. **Observe** — wrap raw input as `Observation` (text, image, etc.)
2. **Abstract** — `TextAbstraction` encodes modalities and extracts anchors → `Scenario`
3. **Collect responses** — human ratings as `SurveyResponse` objects
4. **Map to samples** — convert label strings to numerical rewards `{-1, 0, 1}`
5. **Learn contexts** — `ContextLearner` clusters scenarios by reward distribution (KL/JS divergence) → context labels
6. **Extract features** — `LLMFeatureExtractor` produces semantic feature labels per scenario
7. **Fit generalizer** — `ContextLikelihoodModel` learns feature → context mapping

### Inference path
`Observation` → `TextAbstraction` → `Scenario` → `LLMFeatureExtractor` → `ContextLikelihoodModel.predict_proba()` → `Dict[context, probability]`

---

## Key types

| Type | Location | Description |
|------|----------|-------------|
| `Observation` | `observe/observation.py` | Raw multimodal input |
| `Scenario` | `observe/scenario.py` | Abstracted situation with anchors |
| `SurveySpecification` | `survey/specification.py` | Instructions + response labels |
| `SurveyResponse` | `survey/survey_response.py` | One participant's rating of one scenario (optional `role_perspective`) |
| `HumanSurveyEvaluator` | `evaluation/human_survey.py` | Aggregates CSV survey data |
| `ContextLearner` | `learning/context_learner.py` | MBRL context clustering |
| `LLMFeatureExtractor` | `features/extractor_llm.py` | Semantic feature extraction (stub/LLM) |
| `ContextLikelihoodModel` | `generalize/likelihood.py` | Feature→context likelihood model |
| `CogemiPipeline` | `api.py` | End-to-end pipeline wrapper (role-aware) |
| `role` module | `roles/role.py` | `available_roles`, `filter_by_role`, `is_role_indexed` |

### Context entry structure
```python
contexts_dict: {
    "action_name": {
        "C1": {
            "Distribution": {-1: float, 0: float, 1: float},  # normalized probability
            "Outcomes":     List[float],                        # raw reward samples
            "States":       List[[state_str, reward_samples]]  # provenance
        },
        "C2": { ... }
    }
}
```

### Scenario ID convention
`ContextLearner` expects `scenario.id` in format `"prefix_action_state"` (e.g. `"s_1_2"`), splitting on `_` to extract action (index 1) and state (index 2).

---

## Role support

Scenarios can optionally specify participant roles — **agent** (the one acting), **target** (the recipient), and **observer** (a third party). This allows the pipeline to learn separate context distributions for each perspective.

### Enabling roles

Add a `roles` field to `Scenario` and a `role_perspective` field to each `SurveyResponse`:

```python
from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

scenario = Scenario(
    id="rj_exploit_commission",
    representation="An employer takes all sales commission earned by their employee.",
    anchors={"action": "exploit"},
    roles={"agent": "employer", "target": "salesperson"},
    origin={},
)

responses = [
    SurveyResponse("p1", "rj_exploit_commission", "Just",   role_perspective="agent"),
    SurveyResponse("p2", "rj_exploit_commission", "Unjust", role_perspective="target"),
    SurveyResponse("p3", "rj_exploit_commission", "Unjust", role_perspective="observer"),
]
```

### Role-aware pipeline

`CogemiPipeline.fit()` automatically detects role-indexed responses and fits one sub-pipeline per role. No configuration change is needed.

```python
from cogemi.api import CogemiPipeline
from cogemi.survey.specification import SurveySpecification
from cogemi.evaluation.human_survey import HumanSurveyEvaluator
from cogemi.learning.context_learner import ContextLearner
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.generalize.likelihood import ContextLikelihoodModel
from cogemi.observe.text_abstraction import TextAbstraction

JUDGMENT_MAP = {"Unjust": -1, "Neutral": 0, "Just": 1}

pipeline = CogemiPipeline(
    abstraction=TextAbstraction(model="stub"),
    survey_spec=SurveySpecification(
        instructions={"en": "How just is this action?"},
        response_labels=list(JUDGMENT_MAP.keys()),
        role_instructions={
            "agent":    {"en": "You are the agent. How just is what you are doing?"},
            "target":   {"en": "You are the target. How just is what is being done to you?"},
            "observer": {"en": "You are an observer. How just is the agent's action?"},
        },
    ),
    evaluator=HumanSurveyEvaluator(judgment_map=JUDGMENT_MAP, valid_responses=1),
    learner=ContextLearner(add_threshold=0.5, merge_threshold=0.8, metric="js"),
    feature_extractor=LLMFeatureExtractor(model="stub"),
    generalizer=ContextLikelihoodModel(),
)

pipeline.fit(scenarios, responses)  # auto-detects role mode
```

### Role-indexed contexts

In role mode, `contexts()` returns a dict keyed by role:

```python
contexts = pipeline.contexts()
# {"agent": {action: {"C1": {...}}}, "target": {...}, "observer": {...}}

# Each role has its own distribution
agent_dist   = list(contexts["agent"]["exploit"].values())[0]["Distribution"]
target_dist  = list(contexts["target"]["exploit"].values())[0]["Distribution"]
# agent_dist[1] > target_dist[1]  — agents rate exploitation more favourably
# target_dist[-1] > agent_dist[-1] — targets rate it more harshly
```

### Role-specific prediction

```python
from cogemi.observe.observation import Observation

obs = Observation(
    id="obs_1",
    modalities={"text": "An employer withholds wages from a worker."},
    metadata={},
)

for role in ("agent", "target", "observer"):
    pred = pipeline.predict(obs, role=role)
    # pred: Dict[str, float] — context label → probability, sums to 1.0
```

### Updated data model

| Field | Type | Description |
|-------|------|-------------|
| `Scenario.roles` | `Dict[str, str] \| None` | Maps role names to participant labels, e.g. `{"agent": "employer", "target": "employee"}` |
| `SurveyResponse.role_perspective` | `str \| None` | `"agent"`, `"target"`, `"observer"`, or `None` for non-role surveys |
| `SurveySpecification.role_instructions` | `Dict[str, Dict[str, str]] \| None` | Per-role question text keyed by role then language code |

### Role utility functions

```python
from cogemi.roles.role import available_roles, filter_by_role, is_role_indexed

is_role_indexed(responses)          # True if any response has role_perspective set
available_roles(responses)          # {"agent", "target", "observer"}
filter_by_role(responses, "agent")  # only agent responses
```

### Backward compatibility

Pipelines fitted with non-role responses (`role_perspective=None`) behave exactly as before. `contexts()` returns a flat `ContextsDict` and `predict()` ignores the `role` argument.

---

## Definitions

**Observation** — raw input with one or more modalities (text, image, sound) and metadata.

**Scenario** — abstracted description with a `representation` (e.g. text), `anchors` (e.g. `{"action": "cut_in_line"}`), and provenance `origin`.

**Context** — a cluster of scenarios with similar reward distributions for a given action. Represented as `{Distribution, Outcomes, States}`.

**Dilemma** — legacy term for a scenario with a pre-computed reward distribution: `{Action: str, State: str, Reward: List[int]}`.

---

## Installation

**Requirements:** Python 3.10+, and [Ollama](https://ollama.com/) running locally (or an OpenAI-compatible API).

```bash
# 1. Clone the repository
git clone https://github.com/trondarild/COGEMI_RL.git
cd COGEMI_RL

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the package and dependencies
pip install -e .
```

### LLM configuration

By default COGEMI uses a local Ollama server with the `qwen3:1.7b` model. Copy and edit `cogemi_config.yaml` to change provider or model:

```yaml
llm:
  provider: ollama          # or "openai"
  model: qwen3:1.7b
  base_url: http://localhost:11434
  # api_key: ""             # set here or via COGEMI_API_KEY env var
```

For an OpenAI-compatible API:

```bash
pip install openai
export COGEMI_API_KEY=sk-...
```

Then set `provider: openai` and your chosen `model` in `cogemi_config.yaml`.

### Running tests

```bash
# All tests (LLM tests auto-skip if Ollama is not running)
.venv/bin/python -m pytest tests/ -v

# Stub-only (no Ollama required, ~2 s)
.venv/bin/python -m pytest tests/ -v -k "not ollama"
```

---

## Examples
