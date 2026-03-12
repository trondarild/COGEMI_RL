# tests/test_survey_renderer.py

from cogemi.survey.renderer_text import TextSurveyRenderer
from cogemi.survey.specification import SurveySpecification
from cogemi.observe.scenario import Scenario

def test_text_renderer_output():
    scenario = Scenario(
        id="s1",
        representation="Someone cuts in line.",
        anchors={"action": "cut_in_line"},
        origin={}
    )

    spec = SurveySpecification(
        instructions={"en": "Is this socially appropriate?"},
        response_labels=["No", "Neutral", "Yes"]
    )

    renderer = TextSurveyRenderer()
    rendered = renderer.render(scenario, spec)

    assert rendered["text"] == "Someone cuts in line."
    assert rendered["question"].startswith("Is this")
    assert rendered["responses"] == ["No", "Neutral", "Yes"]
