# COGEMI Progress Summary

## What is COGEMI?

**COGEMI** (Contextual Organisation of General Evaluation from Multimodal Inputs) is a library for learning how humans morally evaluate situations. Given a set of human survey responses, it learns *contextual reward distributions* — how different types of actions in different types of contexts tend to be judged — and generalises these to new, unseen situations.

The library is grounded in three empirical dimensions of moral evaluation:

| Dimension | Survey question | Response scale |
|---|---|---|
| **Social appropriateness** | "Is this behaviour appropriate?" | inappropriate – neutral – appropriate |
| **Justice / fairness** | "Is this fair to the person affected?" | unjust – neutral – just |
| **Effort / energy cost** | "How costly is this for the person affected?" | costly/effortful – neutral – effortless/gainful |

---

## Pipeline

```
Observation (free text)
    ↓  TextAbstraction (LLM)
Scenario(id, description, anchors, roles)
    ↓  LLMFeatureExtractor
Feature labels  ["Deception for gain", "Breach of trust", ...]
    ↓  ContextLearner (MBRL clustering)
Context labels  ["action:C1", "action:C2", ...]
    ↓  ContextLikelihoodModel
P(rating | context)   {-1: 0.7, 0: 0.2, 1: 0.1}
```

`CogemiPipeline` wires all components. Factory methods (`simple_appropriateness_pipeline`, `simple_justice_pipeline`, `simple_effort_pipeline`) provide ready-to-use configurations.

---

## Scenario datasets

Three scenario sources have been prepared, each targeting a different moral dimension.

### 1. Social appropriateness — NormBank

**Source:** [NormBank](https://github.com/socialnormsbank/NormBank) (Ziems et al., 2022)
**Format:** `behaviour` in a `setting`, with contextual constraints (role, consent, severity)
**Scale:** 155 000+ entries; 11 816 unique scenarios loaded into COGEMI
**Loader:** `cogemi/data/normbank.py` → `load_normbank()`

**Example scenarios:**

| Behaviour | Setting | Norm |
|---|---|---|
| kiss someone | running track | appropriate |
| bring a gift | birthday party | appropriate |
| play loud music | library | inappropriate |

Survey question shown to participants:
*"Is it appropriate for a person to [behaviour] in a [setting]?"*

---

### 2. Justice / fairness — SCRUPLES Anecdotes

**Source:** [SCRUPLES](https://github.com/allenai/scruples) (Lourie et al., 2021) — Reddit r/AmITheAsshole
**Format:** Short first-person anecdote titles describing an interpersonal action
**Filter:** Justice-relevant subset — scenarios where a target incurs a quantifiable cost (financial, physical labour, care labour) from the agent's action, raising a question of fair recompense
**Scale:** 27 766 raw anecdotes → ~1 416 justice-filtered scenarios (train split)
**Loader:** `cogemi/data/scruples.py` → `load_justice_subset()`, `select_survey_scenarios()`
**Role support:** agent = story author, target = named relationship (wife, boss, son, …)

**Example scenarios:**

| Scenario | Target | Community verdict |
|---|---|---|
| Expecting my wife to do more of the housework because I bring in more income | wife | unjust (80%) |
| Not paying my friend to be in my short films | friend | ambiguous (52% unjust) |
| Not entirely paying for my son's tuition | son | unjust (74%) |
| Paying for my son to go to college, but not my daughter | daughter | ambiguous (60% unjust) |
| Secretly spending my wife's inheritance | wife | unjust (91%) |

Survey question shown to participants (observer perspective):
*"As an outside observer, is the agent's action towards their [target] just or unjust?"*

---

### 3. Children's books / moral learning — Aesop's Fables

**Source:** *The Aesop for Children* (Rand McNally, 1919), via [Project Gutenberg #19994](https://www.gutenberg.org/ebooks/19994) — public domain
**Format:** 146 fables, each with a one-sentence moral
**Loader:** `cogemi/data/aesop.py` → `load_aesop()`, `extract_scenarios_to_csv()`
**Expansion:** `cogemi/data/aesop_expand.py` converts morals into concrete action-context scenarios via LLM; output in `data/aesop_action_contexts.csv`

**Example fables and morals:**

| Fable | Moral |
|---|---|
| The Wolf and the Kid | Do not let anything turn you from your purpose. |
| The Bundle of Sticks | In unity is strength. |
| The Farmer and the Snake | Learn from my fate not to take pity on a scoundrel. |
| The Gnat and the Bull | The smaller the mind the greater the conceit. |
| The Young Crab and His Mother | Do not tell others how to act unless you can set a good example. |

**LLM-expanded action-context examples** (from `aesop_action_contexts.csv`):

| Action | Context | Rating | Moral |
|---|---|---|---|
| Studying hard despite a personal breakup | Dealing with a breakup while focusing on goals | right | Do not let anything turn you from your purpose. |
| Procrastinating on a project due to anxiety | Feeling overwhelmed by a big exam | wrong | Do not let anything turn you from your purpose. |
| Try to fix a broken fridge without any tools | A household situation where the parent is responsible for maintenance | wrong | Do not attempt the impossible. |
| Offering help to a colleague | Colleague is stuck on a project | right | (various) |

Survey question shown to participants:
*"Is [action] in this context [wrong / neutral / right]?"*

---

## Text length comparability

Survey scenario text lengths compared to the reference COMETH dataset (median 69 chars / 12 words):

| Dataset | Median chars | Median words | vs. reference |
|---|---|---|---|
| Reference (COMETH) | 69 | 12 | — |
| NormBank (as full sentence) | 42 | 9 | 0.61× — OK |
| SCRUPLES justice titles | 58–61 | 11–12 | 0.84–0.88× — OK |
| Aesop morals | 49 | 9 | 0.71× — OK |
| Aesop action+context (combined) | 127 | 21 | 1.84× — too long |

**Note:** For Aesop surveys, display only the `action` field (~65 chars), not the combined `action + context` string.

---

## Role support

All three datasets support the agent / target / observer role framework:

- **NormBank:** single actor (PERSON) in a setting; observer perspective by default
- **SCRUPLES justice:** agent = story author; target = named relationship (extracted via regex); observer = Reddit community voter
- **Aesop:** agent = protagonist; target = affected party; observer = survey participant judging the moral

`Scenario.roles = {"agent": ..., "target": ...}` and `SurveyResponse.role_perspective ∈ {agent, target, observer}` are fully implemented and tested.

---

## Online experiment status

- Survey forms coded and locally tested for all three domains
- Budget prepared for Prolific
- Next step: interface with Prolific and launch live data collection
