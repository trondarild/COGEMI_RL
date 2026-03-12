# cogemi/survey/renderer_text.py

class TextSurveyRenderer:
    def render(self, scenario, survey_spec):
        return {
            "text": scenario.representation,
            "question": survey_spec.instructions[survey_spec.language],
            "responses": survey_spec.response_labels
        }
