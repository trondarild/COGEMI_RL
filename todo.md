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
## Implementation of role-support
- [ ] make a plan for implementing an extention to COGEMI so that it optionally supports scenarios with roles (as mentioned in context-plan.md. 
    - [x] specify clearly what supporting roles entails: each scenario can have at least two roles and possibly three: 1) agent 2) target (or a better label) 3) observer, where agent is the one in the scenario doing something to the target, while the observer is potentially a third party looking on. Example: a) someone (agent) opening door for an old person (target) b) someone (agent) is convinging someone (target) to work for them for a fixed rate and taking all profit c) someone (agent) is pressuring someone (target) to hand over their money d) someone (agent) is using their superior power to make someone (target) perform labor for minimal pay  -> affords asking survery questions like "for the [agent/target] is this situation [unjust] [neutral] [just]" "as an observer do you judge the action of the agent on the target as [unjust] [neutral] [just]" "for the [agent/target] is this situation [effortful,costly] [neutral] [effortless,gainful] in terms of energy"
    - [x] map out which files to modify to implement roles
- [ ] implement support for roles according to the plan
- [ ] implement unit tests for role scenarios
- [ ] iterate unit tests for role support until 100% pass on both previous non-role tests and new role tests
- [ ] create a test data set with 10 actions and 10 contexts for scenarios with roles
- [ ] create a test survery with agent-target permutations using the test data set
- [ ] use the data from test survery to test full pipeline integration test with roles and iterate integration test until 100% pass
- [ ] update readme.md documentation with info about role support
## Data
- [x] read papers.md and skim SCRUPL, NORMBANk papers to get an overview of datasets
- [x] create plan for adapting external datasets to COGEMI (see data/ADAPTATION_PLAN.md)
- [x] implement NormBank loader (cogemi/data/normbank.py) + integration test
- [ ] filter SCRUPLES to create a subset SCRUPLES_JUSTICE that can be transformed to COGEMI appropriate scenarios that can be used in a cogemi role supported survey with 1) unjust - neutral - just 2) energy costly (effortful) - neutral - energy gainful (effortless)
- [ ] implement SCRUPLES Anecdotes loader (cogemi/data/scruples.py) + integration test with role support
- [ ] semantic action clustering (LLM normalisation of raw SCRUPLES action strings)
- [ ] SCRUPLES Dilemmas — defer (pairwise format needs Bradley-Terry or similar)
## Source code control, github
- [x] update .gitignore to exclude unneccesary R files and data files that should be downloaded not stored (SCRUPL, NORMBANK)
- [x] commit current version
- [x] clean up, delete unneccessary files (out.py, out.txt, scratch files in root)
- [x] update and tidy file structure
## Documentation
- [x] update readme.md with installation procedure
## Online experiments
- [ ] prepare online experiments to gather data for social appropriateness
    - [x] make a plan for carrying out experiments
    - [x] prepare budget for Prolific experiment
    - [x] code up experiment forms
    - [x] test experiment
    - [ ] interface with Prolific and set up experiment
    - [ ] pay Prolific and commence live experiment
