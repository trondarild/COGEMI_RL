# Dataset Adaptation Plan

## Summary

| Dataset | Records | Best fit | Mapping effort |
|---------|---------|----------|----------------|
| SCRUPLES Anecdotes | 27,766 | Social appropriateness | Medium |
| SCRUPLES Dilemmas | 23,596 | Justice (pairwise) | High — defer |
| NormBank | 155,423 | Contextual norms | Low — start here |

---

## 1. NormBank → contextual norms pipeline

**Structure:** each row = `(setting, behavior, constraints, norm)`
where `norm ∈ {taboo, normal, expected}`.

**Why start here:** the cleanest structural fit. `behavior` is the action anchor,
`setting` is the state anchor, and the three-way norm maps directly to COGEMI's
{-1, 0, 1} judgment scale. The dataset was explicitly designed to capture how
the *same* behaviour is judged differently across settings — which is exactly
what COGEMI's context learner is meant to discover.

### Mapping

| NormBank field | COGEMI concept |
|----------------|----------------|
| `behavior` | `Scenario.anchors["action"]` |
| `setting` | state (part of `Scenario.id`) |
| `setting-behavior` | `Scenario.representation` |
| `norm` (taboo/normal/expected) | response label → {-1, 0, 1} |
| one row per annotation | one `SurveyResponse` per row |

**Judgment map:** `{"taboo": -1, "normal": 0, "expected": 1}`

**Scenario ID:** `nb_{behavior_slug}_{setting_slug}`
where slugs replace spaces/special chars with underscores.

**Group structure:** group rows by `(behavior, setting)` — each group
becomes one `Scenario` with multiple `SurveyResponse` objects (one per row).

### Implementation steps

1. Write `cogemi/data/normbank.py` — `load_normbank(path) -> tuple[list[Scenario], list[SurveyResponse]]`
2. Slug `behavior` and `setting` strings → `scenario.id` in `nb_{action}_{state}` format
3. Set `Scenario.representation = setting-behavior` (the pre-built combined string)
4. Return one `SurveyResponse` per row, using `norm` as the `response` field
5. Loader should accept optional `split` filter (`"train"`, `"dev"`, `"test"`)
   and optional `min_responses` to drop sparse (behavior, setting) pairs

### Known issues

- **Sparse groups:** many `(behavior, setting)` combinations have only 1–2 annotations.
  Context learning needs enough samples to estimate a distribution. Apply a
  `min_responses` filter (suggest ≥ 5) before loading.
- **Slug collisions:** different behaviors may produce the same slug.
  Keep a collision counter (`nb_{slug}_{slug}_2` etc.) or use a hash suffix.
- **Constraints field:** encodes additional social context (role, characteristic).
  Currently ignore; could later be incorporated as additional anchors.

---

## 2. SCRUPLES Anecdotes → social appropriateness pipeline

**Structure:** each record = one Reddit AITA post.
`action.description` gives a short action summary; `binarized_label_scores`
gives aggregated vote counts `{RIGHT: n, WRONG: m}`.

**Mapping**

| SCRUPLES field | COGEMI concept |
|----------------|----------------|
| `action.description` | `Scenario.anchors["action"]` |
| `text` (full post) or `title` | `Scenario.representation` |
| `id` | state segment of `Scenario.id` |
| `binarized_label_scores` | reconstruct n × RIGHT + m × WRONG responses |
| `RIGHT` | `"Appropriate"` → +1 |
| `WRONG` | `"Inappropriate"` → -1 |

**Scenario ID:** `sc_{action_slug}_{post_id}` — but note: action descriptions are
highly varied (~26K unique), so each scenario effectively has a unique action.
This is too sparse for the context learner to generalise across without LLM
feature extraction doing heavy semantic clustering work.

**Recommendation:** use the LLM feature extractor to group actions into broad
semantic clusters *before* fitting the context learner, rather than relying on
the raw action string as the anchor. Alternatively, restrict the loader to a
thematically coherent subset (e.g., filter by keyword or action cluster).

### Implementation steps

1. Write `cogemi/data/scruples.py` — `load_anecdotes(path) -> tuple[list[Scenario], list[SurveyResponse]]`
2. Expand `binarized_label_scores = {RIGHT: n, WRONG: m}` into `n + m`
   individual `SurveyResponse` objects with synthetic participant IDs
3. Use `action.description` as the action anchor (slugified)
4. Use `title` as `Scenario.representation` (shorter, less noisy than `text`)
5. Skip records where `action` is `null` (~5% of the dataset)
6. Apply `min_responses` filter (suggest ≥ 3)

### Known issues

- **Action diversity:** 26K unique action descriptions means near-zero context
  overlap without LLM-based semantic grouping. Plan to add a pre-clustering
  step using `LLMFeatureExtractor.extract_action()` to normalise action labels.
- **Vote scale:** scores are raw Reddit votes (unbounded), not a fixed panel.
  Very popular posts have hundreds of votes; rare ones have 1–2.
  Apply `max_responses_per_side` cap (e.g., 50) to avoid domination.
- **Label granularity:** the 5-way `label_scores` (AUTHOR / OTHER / EVERYBODY /
  NOBODY / INFO) is richer but harder to map to {-1, 0, 1}. Stick to
  `binarized_label_scores` for now; revisit if the binary signal is too coarse.

---

## 3. SCRUPLES Dilemmas — defer

**Why defer:** each record presents two actions and annotators pick which is
*less ethical* — a relative comparison, not a per-scenario distribution.
This requires converting pairwise preferences into absolute scores, which
introduces assumptions (e.g., Bradley-Terry model) beyond the current scope.

**Possible later path:** join dilemma actions back to their anecdote records via
the shared action `id`, use the anecdote's own score as an absolute anchor,
and use the dilemma's comparison signal to refine context boundaries.

---

## Implementation order

1. **NormBank loader** (lowest friction, best structural fit)
2. **NormBank integration test** — full pipeline fit on a 500-row sample
3. **SCRUPLES Anecdotes loader** — with vote reconstruction and null filtering
4. **Semantic action clustering** — LLM-based normalisation of raw action strings
5. **SCRUPLES Anecdotes integration test**
6. **SCRUPLES Dilemmas** — defer until pairwise-to-distribution conversion is designed
