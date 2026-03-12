# TODO list to complete COGEMI library

## Code quality & correctness
- [x] do type-check for the whole pipeline validating that io signatures compose
- [x] update unit tests after type check so tests actually check if everything ok according to type (now some confusing regarding using dicts vs classes-objects)
- [x] run, iterate unit tests until 100% pass
- [x] make a mermaid diagram of the pipeline, annotated with io types
- [x] update readme.md with an overview of input output types for the whole pipeline
## Core implementation
- [ ] implement llm calls for all placeholders in extractor_llm
- [ ] implement getting the llm provider (ollama or external) and model from an external config file
## Testing
- [ ] write integration tests for: social appropriateness; 
- [ ] write integration tests for: justice-injustice
- [ ] run, iterate on integration tests
## Data
- [ ] read papers.md and skim SCRUPL, NORMBANk papers to get an overview of datasets
- [ ] adapt external datasets as sources of contexts/situations/dilemmas/scenarios: SCRUPL, NORMBANK
## Source code control, github
- [x] update .gitignore to exclude unneccesary R files and data files that should be downloaded not stored (SCRUPL, NORMBANK)
- [x] commit current version
- [ ] clean up, delete unneccessary files (out.py, out.txt, scratch files in root)
- [ ] update and tidy file structure

## Online experiments
- [ ] prepare online experiments to gather data for social appropriateness
    - [ ] prepare budget for Prolific experiment
    - [ ] code up experiment forms
    - [ ] test experiment
