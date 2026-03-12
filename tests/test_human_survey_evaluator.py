# tests/test_human_survey_evaluator.py

import pandas as pd

from cogemi.evaluation.human_survey import HumanSurveyEvaluator
#from cogemi.evaluation.response import SurveyResponse # not needed now

def test_human_survey_aggregation():
    # create a DataFrame matching the columns expected by aggregate()
    # `aggregate` renames columns to ['Timestamp', 'participant_ID', 'Consent',
    #  'question_ID', 'Moral Judgment', 'Age', 'Gender', 'Nationality', 'Group']
    # so we build rows with the same number of entries (we only care about
    # participant_ID, question_ID and Moral Judgment for this test).
    # question_ID format is assumed to be something like "s_1_3" where "1" is 
    # the action code and "3" is the state code. Adjust as needed based on actual format.
    data = [
        [None, "p1", None, "s_1_3", "Appropriate", None, None, None, None],
        [None, "p2", None, "s_1_3", "Neutral", None, None, None, None],
        [None, "p3", None, "s_1_3", "Inappropriate", None, None, None, None],
    ]
    responses = pd.DataFrame(data)

    evaluator = HumanSurveyEvaluator(
        judgment_map={"Inappropriate": -1, "Neutral": 0, "Appropriate": 1},
        valid_responses=1
    )

    dist = evaluator.aggregate(responses)

    assert abs(sum(dist[0]['Reward'])) < 1e-6
    assert dist[0]['Action'] == "1"
    assert dist[0]['State'] == "3"