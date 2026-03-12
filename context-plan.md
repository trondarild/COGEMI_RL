# COGEMI
## Contextual Organization of General Evaluation from Multimodal Inputs

COGEMI is a general-purpose framework for learning **context-sensitive evaluative structure**
from heterogeneous observations and noisy evaluators.

It generalizes the COMETH pipeline by:
- removing text-only assumptions,
- allowing arbitrary evaluation targets (morality, appropriateness, trust, safety),
- supporting multimodal inputs,
- preparing for role-indexed (fibred) evaluation.

The core idea is simple:

> Contexts are equivalence classes of situations induced by stability of evaluation.

Everything else exists to support that construction cleanly.

---

## Conceptual Pipeline

Observation  
→ **Abstraction** (multimodal → semantic)  
→ Scenario (with explicit anchors, like action)  
→ **Evaluation** (scenario → distribution)  
→ **Context learning** (quotients under evaluative similarity)  
→ **Feature extraction** (interpretable descriptors)  
→ **Generalization** (slice-wise left Kan extension)

Roles will later index the entire pipeline as a fibration.

---

## Core Design Principles

1. Multimodality ends before context learning  
2. Evaluation is the only driver of context induction  
3. Anchors (actions, interaction types, etc.) are explicit objects  
4. Context learning is role-local  
5. Cross-role comparison happens after learning  
6. All components are pluggable and testable

---

## Module Overview

cogemi/
│
├── observe/ # Observation → Scenario abstraction
├── anchors/ # Slicing logic, typically for action
├── evaluation/ # Evaluators (human, model, rule-based)
├── learning/ # Context learning (adding / merging)
├── metrics/ # Divergences and distances
├── features/ # Interpretable feature extraction
├── generalize/ # Likelihood-based generalization
├── roles/ # Role fibration (future)
└── api.py # High-level orchestration


---
## Survey Construction and Human Evaluation

COGEMI treats survey construction as a **first-class component** of the pipeline.
Human judgment is not accessed directly; it is mediated by presentation, instructions,
and response affordances. These must therefore be explicit and versioned.

### Position in the Pipeline

Observation  
→ Abstraction → Scenario  
→ **Survey Rendering**  
→ Participant Response  
→ Evaluation Distribution  
→ Context Learning

Survey design directly shapes the evaluation functor and must be controlled.

---

### SurveySpecification

A `SurveySpecification` defines how scenarios are presented and how responses are collected.

It includes:
- instructions (per language),
- response space (e.g. blame / neutral / support),
- presentation template (textual or multimodal),
- randomization and grouping rules,
- required metadata (age, role, etc.).

Survey specifications are declarative and backend-agnostic.

---

### Survey Rendering

Rendering is handled by a `SurveyRenderer` that maps:

Scenario × SurveySpecification × Language  
→ Human-facing survey item

Renderers may target:
- HTML (e.g. Google Apps Script),
- Qualtrics,
- Prolific,
- lab software,
- or simulated evaluators.

---

### Responses and Evaluation

Raw participant responses are stored as structured `SurveyResponse` objects.
Evaluators aggregate responses into evaluation distributions used by context learning.

No learning component accesses raw survey infrastructure directly.

---


### Design Constraints

- Survey wording must not depend on learned contexts
- Presentation choices must be auditable
- Multiple survey designs may coexist for the same scenario set
- Role and language must be explicit metadata, not implicit grouping


## Immediate TODOs (Implementation Order)

## Survey Layer

- [x] Define `SurveySpecification` data class
- [x] Define `SurveyRenderer` interface
- [ ] Refactor existing HTML / Apps Script survey into a renderer backend
- [ ] Formalize response schemas and metadata handling
- [ ] Add versioning for survey wording and instructions
- [ ] Ensure compatibility with multimodal scenarios


### Phase 1 — Core abstractions
- [ ] Implement `Observation`
- [x] Implement `Scenario`
- [ ] Define `ObservationAbstraction` interface
- [ ] Create a text-only abstraction (COMETH baseline)

### Phase 2 — Context learning core
- [x] Refactor context learner into a pure class
- [x] Implement divergence metrics as standalone functions
- [x] Remove notebook state and globals

### Phase 3 — Feature extraction & generalization
- [x] Define `FeatureExtractor` interface
- [ ] Implement LLM-based extractor
- [ ] Refactor likelihood generalization into a class

### Phase 4 — Pipeline API
- [ ] Implement `CogemiPipeline`
- [ ] Support anchor-based slicing
- [ ] Enable partial pipeline calls (e.g. contexts only)

### Phase 5 — Multimodal readiness
- [ ] Add modality encoder interfaces
- [ ] Stub vision/audio encoders
- [ ] Ensure modality-agnostic downstream behavior

### Phase 6 — Roles (later)
- [ ] Define role base category
- [ ] Index pipelines by role
- [ ] Implement cross-role comparison tools

---

## What COGEMI Is Not

- Not a classifier
- Not a rule-based ethics engine
- Not tied to human judgment
- Not tied to text

COGEMI is an **organizational principle** for evaluative structure.

---

## Minimal Working Example (Target)

```python
pipeline = CogemiPipeline(
    abstraction=TextAbstraction(),
    evaluator=HumanSurveyEvaluator(),
    anchor="action"
)

pipeline.fit(observations, judgments)
contexts = pipeline.contexts()
prediction = pipeline.predict(new_observation)
```