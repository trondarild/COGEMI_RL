# TODO list to complete COGEMI library

## Code quality & correctness
- [x] do type-check for the whole pipeline validating that io signatures compose
- [x] update unit tests after type check so tests actually check if everything ok according to type (now some confusing regarding using dicts vs classes-objects)
- [x] run, iterate unit tests until 100% pass
- [x] make a mermaid diagram of the pipeline, annotated with io types
- [x] update readme.md with an overview of input output types for the whole pipeline
## Core implementation
- [x] implement llm calls for all placeholders in extractor_llm
- [x] implement getting the llm provider (ollama or external) and model from an external config file
## Testing
- [x] write integration tests for: social appropriateness; justice-injustice
- [x] run, iterate on integration tests
## Validation
- [x] validate that text-length for social-appropriateness, justice, children's-book scenarios is comparable to that of /Users/trond/code/COMETH_RL/scenarios_dataset.csv
## Implementation of role-support
- [x] make a plan for implementing an extention to COGEMI so that it optionally supports scenarios with roles (as mentioned in context-plan.md. 
    - [x] specify clearly what supporting roles entails: each scenario can have at least two roles and possibly three: 1) agent 2) target (or a better label) 3) observer, where agent is the one in the scenario doing something to the target, while the observer is potentially a third party looking on. Example: a) someone (agent) opening door for an old person (target) b) someone (agent) is convinging someone (target) to work for them for a fixed rate and taking all profit c) someone (agent) is pressuring someone (target) to hand over their money d) someone (agent) is using their superior power to make someone (target) perform labor for minimal pay  -> affords asking survery questions like "for the [agent/target] is this situation [unjust] [neutral] [just]" "as an observer do you judge the action of the agent on the target as [unjust] [neutral] [just]" "for the [agent/target] is this situation [effortful,costly] [neutral] [effortless,gainful] in terms of energy"
    - [x] map out which files to modify to implement roles
- [x] implement support for roles according to the plan
- [x] implement unit tests for role scenarios
- [x] iterate unit tests for role support until 100% pass on both previous non-role tests and new role tests
- [x] create a test data set with 10 actions and 10 contexts for scenarios with roles
- [x] create a test survery with agent-target permutations using the test data set
- [x] use the data from test survery to test full pipeline integration test with roles and iterate integration test until 100% pass
- [x] update readme.md documentation with info about role support
## Data
- [x] read papers.md and skim SCRUPL, NORMBANk papers to get an overview of datasets
- [x] create plan for adapting external datasets to COGEMI (see data/ADAPTATION_PLAN.md)
- [x] implement NormBank loader (cogemi/data/normbank.py) + integration test
- [x] filter SCRUPLES to create a subset SCRUPLES_JUSTICE that can be transformed to COGEMI appropriate scenarios that can be used in a cogemi role supported survey with 1) unjust - neutral - just 2) energy costly (effortful) - neutral - energy gainful (effortless)
- [x] implement SCRUPLES Anecdotes loader (cogemi/data/scruples.py) + integration test with role support
- [x] prepare SCRUPLES justice dataset suitable for generating prolific surveys
- [x] create local html survey file with questions from the created SCRUPLES justice dataset
- [x] write out to csv files the cogemi versions of normbank, scruples, aesops datasets if not already done
- [x] normbank: cluster unique actions
- [ ] semantic action clustering (LLM normalisation of raw SCRUPLES action strings)
- [ ] SCRUPLES Dilemmas — defer (pairwise format needs Bradley-Terry or similar)
### Morals from childrens books
 - [x] research the possibility to download free childrens books with moral content from online repositories
 - [x] download a free children's book with moral content
 - [x] extract cogemi scenarios from children's book
 - [x] put scenarios in csv file
## github, Source code control
- [x] update .gitignore to exclude unneccesary R files and data files that should be downloaded not stored (SCRUPL, NORMBANK)
- [x] commit current version
- [x] clean up, delete unneccessary files (out.py, out.txt, scratch files in root)
- [x] update and tidy file structure
- [x] add cogemi*.csv, aesop*.csv in data folder to github; modify .gitignore appropriately
## Documentation
- [x] update readme.md with installation procedure
## Online experiments
- [x] update local test html surveys with contextual question: after rating a scenario according to the ternary scale, the survey should present a question "what is the contextual element which made you judge the situation the way you did - please click on the relevant part(s) of the text in order of importance". Each word in the text should now be clickable and both words and the order of clicks should be saved to the csv file
- [x] aspect-click variant of the contextual question: instead of clicking words, participant ranks three pre-generated aspects of the scenario in order of importance; all three must be clicked before Continue is enabled
    - [x] select 80 scenarios for manual aspect processing — redesigned as 1×8×5 structure per GM's PDF proposal: Part 1 = 1 behavior (yell) × 8 settings × 5 agent constraints; Part 2 = 1 setting (park) × 8 behaviors × 5 agent constraints
    - [x] put each half (40) into `data/scenarios_manual_processing_1.md` and `data/scenarios_manual_processing_2.md`
    - [x] send `scenarios_manual_processing_1.md` to GM
    - [x] process `scenarios_manual_processing_2.md` TAT
    - [x] offline aspect generation: manually processed for park scenarios (Part 2); aspects stored as `aspect_a`, `aspect_b`, `aspect_c` in survey HTML
    - [x] update survey HTML: `appropriateness_survey_aspects_park.html` — park scenarios, aspect-ranking UX
    - [x] save aspect ranking to Supabase: stored as pipe-separated ordered string in `aspect_ranking` column
- [x] prepare online experiments to gather data for social appropriateness
    - [x] make a plan for carrying out experiments
    - [x] prepare budget for Prolific experiment
    - [x] code up experiment forms
    - [x] test experiment
    - [x] record Prolific URL params: `PROLIFIC_PID`, `STUDY_ID`, `SESSION_ID` captured silently from URL and stored with every Supabase row
    - [x] create Prolific pilot HTML (`appropriateness_survey_aspects_park_prolific.html`): no demographics, URL param gate, completion code input + redirect
        - [x] remove the demographics page entirely
        - [x] gate entry on valid URL params
        - [x] on completion, participant pastes code → stored in Supabase + redirect to `PROLIFIC_RETURN_URL?cc=<code>`
        - [x] add `study_id`, `session_id`, `completion_code` columns to Supabase `responses` table (migration SQL in `appropriateness_survey_supabase_setup.sql`)
        - [x] move all survery files to trondarild.github.io/cavaa/
        - [x] time doing survey with 42 questions — TAT completed in 10:05 min
        - [x] estimate cost/payment based on total time — 10 min at £9/hr = £1.50 minimum; recommend £1.80–£2.00 to be above Prolific minimum
    - [x] push park survey to GitHub Pages
    - [x] fill in actual `PROLIFIC_RETURN_URL` in `appropriateness_survey_aspects_park_prolific.html` — set to https://app.prolific.com/submissions/complete?cc=CMZU9JD5
    - [x] Prolific preview underway
    - [x] fill in Prolific study registration info (see `data/prolific-survey-info.md`):
        - [x] study name (shown to participants)
        - [x] internal study name (researcher-facing only)
        - [x] study description (shown to participants on Prolific before they accept)
    - [x] create role-perspective variant (`appropriateness_survey_aspects_park_role_prolific.html`): `?role=agent|target|observer` URL param, saves to `role_responses` table
        - [x] add `study_id`, `session_id`, `completion_code`, `aspect_ranking` columns to `role_responses` (migration SQL in `appropriateness_survey_supabase_setup.sql`)
        - [ ] run Supabase migration for `role_responses` new columns before going live
        - [ ] push role survey to GitHub Pages
        - [ ] register role survey as separate Prolific study (or sub-condition) with updated survey URL including `?role=` param
    - [ ] update contexts: add that it's a special case when appropriate (e.g. a person leaving litter when get upsetting phone call)
    - [ ] approve pilot and pay Prolific to commence live experiment
## Reference-level instrument upgrades (see reference-level-survey-requirements.md)
### Survey HTML changes — implemented in `appropriateness_survey_aspects_park_prolific_v2.html`
- [x] **Construct separation** (non-optional per Bicchieri measurement standards)
    - [x] add Q2 injunctive norm: "What do most people think?" (5-point Likert)
    - [x] add Q3 empirical expectation: "How often do people actually do this?" (Rarely / Sometimes / Often)
    - [x] present Q1→Q2→Q3→confidence sequentially before aspect phase
    - [x] store `norm_type` ("personal" | "injunctive" | "empirical") as a column in `responses_v2`
- [x] **Response scale anchoring** — 5-point Likert for Q1 and Q2; discretize to {-1, 0, 1} in pipeline
    - [x] HTML response buttons: Strongly inappropriate → Strongly appropriate (5 levels)
    - [x] `response_value` integer column in `responses_v2` (stores raw 1–5)
- [x] **Confidence / uncertainty rating** — "How certain are you?" (1–5) after each scenario's rating block
    - [x] `confidence` column in `responses_v2`
- [x] **Test-retest reliability** — 5 scenarios repeated at end of survey, flagged `is_repeat = true`
    - [x] scenarios span valence range: yell_park_drunk, litter_park_drunk, yell_park_child, alcohol_park_performer, cry_park_distress
    - [x] appended after position 42 (total session: 47 items)
    - [x] `is_repeat` boolean column in `responses_v2`
- [x] **Perceived disagreement** — 1–5 probe every 10 main scenarios; stored in `responses_v2`
### v2 database
- [x] design `responses_v2` table with full v2 schema (no ALTER TABLE migrations needed)
    - [x] SQL in `appropriateness_survey_supabase_setup.sql`, includes RLS anon-insert policy
- [ ] **create `responses_v2` table in Supabase** — run `CREATE TABLE responses_v2` block from `appropriateness_survey_supabase_setup.sql` in Supabase SQL editor
- [ ] test v2 survey end-to-end against live `responses_v2` table (check rows appear with correct norm_type, response_value, confidence, is_repeat)
- [ ] push `appropriateness_survey_aspects_park_prolific_v2.html` to GitHub Pages
- [ ] update `data/prolific-survey-info.md` with v2 timing (~20–25 min) and recommended reward (~£3.00–£3.75)
### Pipeline changes
- [x] add `norm_type: Optional[str]` field to `SurveyResponse` — "personal" | "injunctive" | "empirical"
- [x] add `confidence: Optional[int]` field to `SurveyResponse`
- [x] add `cogemi/metrics/reliability.py` module:
    - [x] `likert_to_ternary(value, scale=5)` — maps 1–5 Likert to {-1, 0, 1}
    - [x] `discretize_likert_responses(samples, scale=5)` — batch conversion
    - [x] `distributional_consistency(dist_a, dist_b)` — JS divergence between two repeat-item distributions
    - [x] `within_scenario_reliability(distributions)` — mean pairwise JS across repeated items
- [x] add `norm_type`-aware routing in `CogemiPipeline.fit()`: when responses carry `norm_type`, fit separate sub-pipelines per type (analogous to role mode)
- [x] write unit + integration tests for all new pipeline additions (`tests/test_reference_spec.py`, 41 tests)
- [ ] add confidence-weighted distribution estimator: up-weight high-confidence responses when computing `estimate_distribution()`
- [ ] add reliability reporting: given a set of repeated-item responses, compute and report mean JS consistency
- [ ] update `HumanSurveyEvaluator` to accept a 5-point Likert judgment map and discretize internally via `likert_to_ternary()`
### Gaps vs. example-ref-level-vignette.md (priority order)
- [ ] **Q4 — Expected sanction** (low effort, high impact): add 5-point phase "If someone objected to this action, how likely is it that others nearby would disapprove of the objection?" — distinguishes "action is appropriate" from "objecting violates the local norm"; save as `norm_type="sanction"` row in `responses_v2`
- [ ] **Q3 — Replace 3-point empirical with 0–100 slider**: "Out of 100 people in this situation, how many do you think would react positively?" — continuous estimate gives richer empirical distribution; store as `response_value` integer 0–100
- [ ] **Q6 — Perceived disagreement per item**: remove every-10-scenario gate; ask after every scenario's confidence phase; small time cost but substantially richer uncertainty data
- [ ] **Calibration / anchoring vignettes**: add 4 fixed scenarios (positive anchor, negative anchor, boundary contrast, paraphrase repeat of one main scenario) to orient participants and enable cross-participant calibration; insert at fixed positions independent of shuffle
- [ ] **Q7 — Forced-choice action ranking** (high effort, high RL value): for each scenario present 4–5 alternative actions and ask participant to rank from most to least appropriate; gives preference ordering suitable for Bradley-Terry / policy learning; requires per-scenario action alternatives to be authored
- [ ] **Structured context schema**: store context dimensions as queryable fields alongside each row — `behavior`, `agent_constraint`, `setting`; can be derived from `scenario_id` at insert time in JS rather than requiring schema change
## Communication and collaboration
- [x] summarise progress so far and give examples of current scenario-data for social-appropriateness, morals-from-children's-books, justice
- [ ] meeting with MK and GM — scheduled 2026-04-29 14:00 (follow up on outcomes)
    - [ ] paper framing discussion: draft a shared understanding of the narrative
        - [ ] what claim does the paper make? (e.g. contextual norms can be learned from human judgements and generalised to new situations via semantic features)
        - [ ] what is the key contribution? (e.g. COGEMI pipeline + dataset + evidence that agent identity / setting modulate appropriateness systematically)
        - [ ] why does it matter? (e.g. for value alignment in RL agents, social robotics, AI safety — grounding reward in human contextual norms rather than fixed rules)
        - [ ] which results will we show? (e.g. ternary distributions per scenario cluster, aspect-ranking patterns, cross-setting generalisation)
        - [ ] propose integration of pipeline outputs (generalisations etc) with broader CAVAA architecture - how it fits with the decision-making part and can be used to bias action selection
        - [ ] which venue / audience? (e.g. CogSci, NeurIPS alignment workshop, ICDL, IROS)
    - [ ] GM to process Part 1 scenarios (yell × 8 settings) — aspects for `scenarios_manual_processing_1.md`

## From meetings
- [x] check if Prolific has template for survey, or if can use google forms
    - [x] can Prolific support context word ordering in template
- [x] how to estimate pay - do we set a max paid time and they only get money if they complete the survey?
- [x] how to decide which actions and contexts from normbank to include in survey? for pilot want 5 actions w 20 contexts
