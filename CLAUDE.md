# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run a single test file
.venv/bin/python -m pytest tests/test_integration.py -v

# Run a single test by name
.venv/bin/python -m pytest tests/ -v -k "test_pipeline_integration"

# Install dependencies (first-time setup)
.venv/bin/pip install -e .
```

Tests run in ~1–2 s (stub mode) or ~50 s when live Ollama tests fire. Ollama tests auto-skip if the server is not running on `localhost:11434`.

## Architecture

COGEMI learns **contextual reward distributions** from human survey data and generalises them to new situations via semantic features.

### Pipeline data flow

```
Observation  →  TextAbstraction  →  Scenario
                                        │
               SurveyResponse[]  →  map_responses_to_samples()  →  List[List[float]]
                                        │
                              ContextLearner.fit()  →  context labels (List[str])
                                        │
                    LLMFeatureExtractor.extract_from_scenario()  →  features (List[str])
                                        │
                         ContextLikelihoodModel.fit(features, labels)
                                        │
                         ContextLikelihoodModel.predict_proba(features)  →  Dict[str, float]
```

`CogemiPipeline` in `cogemi/api.py` wires all components together. Factory methods (`simple_appropriateness_pipeline`, `simple_justice_pipeline`, `simple_effort_pipeline`) cover common use cases. The pipeline is dimension-agnostic — only the `judgment_map` and `response_labels` differ between social appropriateness, justice, etc.

### Key constraints and conventions

**Scenario ID format:** `ContextLearner` splits `scenario.id` on `_` and takes index 1 as the action and index 2 as the state. IDs must be in `"prefix_action_state"` form (e.g. `"s_cutline_supermarket"`).

**Context label format:** After `ContextLearner.fit()`, returned labels are strings like `"action:C1"`. These are the `y` values passed to `ContextLikelihoodModel.fit()`.

**Distribution type:** `Dict[int, float]` with keys `{-1, 0, 1}`, always normalised to sum to 1. Used throughout `learning/` and `metrics/`.

**Stub mode:** Pass `model="stub"` to `LLMFeatureExtractor` or `TextAbstraction` to skip all LLM calls. Always use stub mode in tests that don't specifically test LLM behaviour.

**Two separate `SurveyResponse` classes exist:**
- `cogemi/survey/survey_response.py` — used throughout the pipeline (has `response: str` field)
- `cogemi/evaluation/response.py` — `EvaluationSurveyResponse`, inherits `Observation`, not currently wired into the pipeline

### LLM configuration

`cogemi/config.py` searches for `cogemi_config.yaml` in: explicit path → `COGEMI_CONFIG` env var → `./cogemi_config.yaml` → `~/.cogemi_config.yaml`. `COGEMI_API_KEY` env var overrides `api_key` from file. Supported providers: `ollama` (default), `openai` (requires `pip install openai`).

### `thresholds.py` vs `context_learner.py`

`cogemi/learning/thresholds.py` is a **legacy module** ported from notebooks. It contains standalone functions (`MBRL_agent`, `input_dilemma`, `merge`, `grid_search_thresholds`) used for hyperparameter search. The active pipeline uses `ContextLearner` in `context_learner.py` instead. `Reward` in `thresholds.py` dilemma dicts must be a **list of sample values** (e.g. `[-1, -1, 0, 1]`), not a pre-computed distribution dict.
