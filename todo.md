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
### Survey HTML changes
- [ ] **Construct separation** (non-optional per Bicchieri measurement standards)
    - [ ] add Q2 injunctive norm: "What do you think most people in this situation would consider appropriate?" (same ternary/Likert scale)
    - [ ] add Q3 empirical expectation: "How often do you think people actually behave this way?" (Rarely / Sometimes / Often)
    - [ ] present Q1→Q2→Q3 sequentially after each scenario before moving to aspect phase
    - [ ] store `norm_type` ("personal" | "injunctive" | "empirical") as a column alongside each row in Supabase
- [ ] **Response scale anchoring** — replace ternary with 5-point Likert for Q1 and Q2 to allow variance estimation; discretize to {-1, 0, 1} in pipeline
    - [ ] update HTML response buttons to 5 levels (Strongly Inappropriate → Strongly Appropriate)
    - [ ] add SQL migration for new `response_value` integer column in Supabase (store raw 1–5 alongside text label)
- [ ] **Confidence / uncertainty rating** — after each ternary/Likert response, ask "How certain are you?" (1=Not at all, 5=Very certain)
    - [ ] add `confidence` column to Supabase `responses` table (SQL migration)
    - [ ] store confidence value with each row
- [ ] **Test-retest reliability** — repeat 5 scenarios at the end of the survey (participants see them twice, spaced apart)
    - [ ] select 5 representative scenarios spanning valence range
    - [ ] insert them as duplicates at positions 35–40 (after the main 40 are complete)
    - [ ] flag repeated items with `is_repeat: true` column in Supabase
- [ ] **Perceived disagreement** — add one item per 10 scenarios: "How much do you think people would disagree on this?" (1=Strong consensus → 5=Lots of disagreement)
    - [ ] store as `perceived_disagreement` column (integer) in Supabase
### Pipeline changes
- [x] add `norm_type: Optional[str]` field to `SurveyResponse` — "personal" | "injunctive" | "empirical"
- [x] add `confidence: Optional[int]` field to `SurveyResponse`
- [x] add `cogemi/metrics/reliability.py` module:
    - [x] `likert_to_ternary(value, scale=5)` — maps 1–5 Likert to {-1, 0, 1}
    - [x] `discretize_likert_responses(samples, scale=5)` — batch conversion
    - [x] `distributional_consistency(dist_a, dist_b)` — JS divergence between two repeat-item distributions
    - [x] `within_scenario_reliability(distributions)` — mean pairwise JS across repeated items
- [x] add `norm_type`-aware routing in `CogemiPipeline.fit()`: when responses carry `norm_type`, fit separate sub-pipelines per type (analogous to role mode)
- [ ] add confidence-weighted distribution estimator: up-weight high-confidence responses when computing `estimate_distribution()`
- [ ] add reliability reporting: given a set of repeated-item responses, compute and report mean JS consistency
- [ ] update `HumanSurveyEvaluator` to accept a 5-point Likert judgment map and discretize internally via `likert_to_ternary()`
## Communication and collaboration
- [x] summarise progress so far and give examples of current scenario-data for social-appropriateness, morals-from-children's-books, justice
- [ ] meeting with MK and GM — 2026-04-29 14:00
    - [ ] prepare progress report: what is done, what is running (Prolific pilot), what is next
    - [ ] prepare demo material: show live survey on GitHub Pages, show Supabase data, walk through scenario structure (1×8×5 design)
    - [ ] outline path forward: GM processes Part 1 scenarios (yell × 8 settings), pilot results → full experiment, pipeline integration
    - [ ] paper framing discussion: draft a shared understanding of the narrative
        - [ ] what claim does the paper make? (e.g. contextual norms can be learned from human judgements and generalised to new situations via semantic features)
        - [ ] what is the key contribution? (e.g. COGEMI pipeline + dataset + evidence that agent identity / setting modulate appropriateness systematically)
        - [ ] why does it matter? (e.g. for value alignment in RL agents, social robotics, AI safety — grounding reward in human contextual norms rather than fixed rules)
        - [ ] which results will we show? (e.g. ternary distributions per scenario cluster, aspect-ranking patterns, cross-setting generalisation)
        - [ ] propose integration of pipeline outputs (generalisations etc) with broader CAVAA architecture - how it fits with the decision-making part and can be used to bias action selection
        - [ ] which venue / audience? (e.g. CogSci, NeurIPS alignment workshop, ICDL, IROS)

## From meetings
- [x] check if Prolific has template for survey, or if can use google forms
    - [x] can Prolific support context word ordering in template
- [x] how to estimate pay - do we set a max paid time and they only get money if they complete the survey?
- [x] how to decide which actions and contexts from normbank to include in survey? for pilot want 5 actions w 20 contexts
