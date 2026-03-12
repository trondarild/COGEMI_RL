# tests/test_pipeline.py

from cogemi.api import CogemiPipeline
# from cogemi.observe.text_abstraction import TextAbstraction
# from cogemi.survey.specification import SurveySpecification
# from cogemi.evaluation.human_survey import HumanSurveyEvaluator
# from cogemi.observe.observation import Observation
from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

def test_pipeline_smoke():
    pipeline = CogemiPipeline.simple_appropriateness_pipeline()

    # Create some dummy scenarios and survey responses to fit the pipeline
    # note: this could also be "observations" which would be less processed scenario descriptions, 
    # but would then need to be put through the abstraction step in the pipeline.
    scenarios = [
        Scenario(id="s_1_2", representation="Someone interrupts politely.", anchors={"action": "interrupt_politely"},
        origin={"observation_id": "o1"}),
        Scenario(id="s_2_1", representation="Someone interrupts aggressively.", anchors={"action": "interrupt_aggressively"},
        origin={"observation_id": "o2"}),
    ]

    responses = [
        SurveyResponse(participant_id="p1", scenario_id="s_1_2", response="Appropriate"),
        SurveyResponse(participant_id="p2", scenario_id="s_1_2", response="Neutral"),
        SurveyResponse(participant_id="p3", scenario_id="s_2_1", response="Inappropriate"),
        SurveyResponse(participant_id="p4", scenario_id="s_2_1", response="Inappropriate")
    ]

    # test map_responses_to_samples
    samples = pipeline.map_responses_to_samples(responses)
    
    assert len(samples) == 2 # we have two scenarios, so we should have two samples
    assert samples[0][0] == 1 # the first scenario has one "Appropriate" response, which maps to 1
    assert samples[0][1] == 0 # the first scenario has one "Neutral
    assert samples[1][0] == -1 # the second scenario has two "Inappropriate" responses, which maps to -1    
    assert samples[1][1] == -1

    pipeline.fit(scenarios, responses)

    contexts = pipeline.contexts()
    assert len(contexts) >= 1
