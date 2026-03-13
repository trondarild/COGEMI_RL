# cogemi/survey/renderer_text.py

class TextSurveyRenderer:
    def render(self, scenario, survey_spec, role_perspective=None):
        return {
            "text": scenario.representation,
            "question": survey_spec.instruction_for(role_perspective),
            "responses": survey_spec.response_labels,
            "role_perspective": role_perspective,
        }
