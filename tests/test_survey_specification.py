# tests/test_survey_specification.py

from cogemi.survey.specification import SurveySpecification

def test_survey_specification_basic():
    spec = SurveySpecification(
        instructions={"en": "How appropriate is this action?"},
        response_labels=["Inappropriate", "Neutral", "Appropriate"]
    )

    assert spec.instructions["en"].startswith("How appropriate")
    assert len(spec.response_labels) == 3
    assert spec.language == "en"
    assert spec.metadata_fields == []
