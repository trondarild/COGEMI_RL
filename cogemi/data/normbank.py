# cogemi/data/normbank.py
"""
NormBank dataset loader.

NormBank (Ziems et al., 2022) contains 155,423 crowd-sourced norm annotations.
Each row has `setting`, `behavior`, and `norm` ∈ {taboo, normal, expected}.

This loader groups rows by (behavior, setting), producing one Scenario per
group and one SurveyResponse per row (annotator judgment).

Scenario ID format: ``nb_{b_idx}_{s_idx}``
  - b_idx: integer index of the unique behavior string
  - s_idx: integer index of the unique setting string
This avoids underscore collisions with ContextLearner's ``split("_")`` parsing.

Judgment map (for use with HumanSurveyEvaluator):
  {"taboo": -1, "normal": 0, "expected": 1}
"""

from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

JUDGMENT_MAP = {"taboo": -1, "normal": 0, "expected": 1}


def load_normbank(
    path: str | Path,
    split: Optional[str] = None,
    min_responses: int = 5,
    max_rows: Optional[int] = None,
) -> Tuple[List[Scenario], List[SurveyResponse]]:
    """Load NormBank and return (scenarios, survey_responses).

    Parameters
    ----------
    path:
        Path to ``NormBank.csv``.
    split:
        If given, filter to rows where the ``split`` column equals this value
        (e.g. ``"train"``, ``"test"``).
    min_responses:
        Drop (behavior, setting) groups with fewer than this many rows.
        Default 5 ensures each scenario has enough signal.
    max_rows:
        If given, sub-sample up to this many rows from the (filtered) CSV
        before grouping. Useful for quick integration tests.

    Returns
    -------
    scenarios:
        One ``Scenario`` per (behavior, setting) group that passes
        ``min_responses``.
    survey_responses:
        One ``SurveyResponse`` per row, keyed to the matching scenario ID.
        The ``response`` field is the raw norm string (``"taboo"`` /
        ``"normal"`` / ``"expected"``).
    """
    df = pd.read_csv(path)

    if split is not None:
        df = df[df["split"] == split].reset_index(drop=True)

    # Keep only rows with a valid norm value
    df = df[df["norm"].isin(JUDGMENT_MAP)].reset_index(drop=True)

    if max_rows is not None:
        df = df.head(max_rows)

    # Build integer indices for unique behaviors and settings
    behaviors = {b: i for i, b in enumerate(df["behavior"].unique())}
    settings = {s: i for i, s in enumerate(df["setting"].unique())}

    scenarios: List[Scenario] = []
    survey_responses: List[SurveyResponse] = []

    for (behavior, setting), group in df.groupby(["behavior", "setting"], sort=False):
        if len(group) < min_responses:
            continue

        b_idx = behaviors[behavior]
        s_idx = settings[setting]
        scenario_id = f"nb_{b_idx}_{s_idx}"

        scenario = Scenario(
            id=scenario_id,
            representation=f"{setting}: {behavior}",
            anchors={"action": behavior, "setting": setting},
            origin={"source": "normbank"},
        )
        scenarios.append(scenario)

        for row_idx, row in group.iterrows():
            survey_responses.append(
                SurveyResponse(
                    participant_id=f"nb_annotator_{row_idx}",
                    scenario_id=scenario_id,
                    response=row["norm"],
                )
            )

    return scenarios, survey_responses
