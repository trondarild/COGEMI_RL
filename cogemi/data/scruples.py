# cogemi/data/scruples.py
"""
SCRUPLES Anecdotes dataset loader.

SCRUPLES Anecdotes (Lourie et al., 2020) contains ~27,766 real-life anecdotes
from Reddit's r/AmITheAsshole, each annotated with community votes on whether
the author was in the wrong.

Two loaders are provided:

1. ``load_anecdotes`` — general loader.
   Judgment map: ``{"Right": 1, "Wrong": -1}``

2. ``load_justice_subset`` — filters to interpersonal scenarios with a clear
   agent-target dynamic, suitable for justice and effort dimension surveys
   with role support (agent / target / observer).
   Judgment map: ``JUSTICE_JUDGMENT_MAP = {"Just": 1, "Neutral": 0, "Unjust": -1}``
   Note: SCRUPLES votes map to Just (RIGHT) and Unjust (WRONG) only — no
   Neutral responses are present in the raw data.

Scenario ID format: ``sc_{action_idx}_{post_id}``
  - action_idx: integer index of the unique action description string
  - post_id: Reddit post ID (alphanumeric, no underscores)
This ensures ``split("_")[1]`` and ``split("_")[2]`` give the action and state
segments expected by ``ContextLearner``.

For ``load_justice_subset``, the prefix is ``scj`` instead of ``sc``, and each
``SurveyResponse`` carries ``role_perspective="observer"`` (the Reddit community
acts as a third-party observer when voting).
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

# ---------------------------------------------------------------------------
# Judgment maps
# ---------------------------------------------------------------------------

JUDGMENT_MAP: dict = {"Right": 1, "Wrong": -1}
JUSTICE_JUDGMENT_MAP: dict = {"Just": 1, "Neutral": 0, "Unjust": -1}

# ---------------------------------------------------------------------------
# Justice-relevance filter
# ---------------------------------------------------------------------------
#
# A scenario is justice-relevant (in the energy/effort/recompense sense) when:
#   • the target incurs a quantifiable cost — financial, physical labour, or
#     care/emotional labour — due to the agent's action or inaction, AND
#   • the scenario raises the question of whether that cost was fairly
#     compensated or acknowledged.
#
# Purely normative scenarios (moral right/wrong without a measurable cost
# structure, e.g. "telling my sister to get over a breakup") are excluded.
#
# The filter is applied only to the action description + title, NOT the full
# post body, to avoid false positives from incidental keyword occurrences.

_JUSTICE_RE = re.compile(
    r"\b("
    # --- Financial obligations / monetary cost ---
    r"pay|paid|paying|payment|underpay|overpay|"
    r"wage|wages|salary|commission|bonus|overtime|"
    r"rent|tuition|fee|fees|tip|tipping|debt|owe|owed|owing|bill|bills|"
    r"loan|refund|money|child\s+support|alimony|maintenance|"
    # 'spending' only in financial context (not 'spending the day/time/night')
    r"spending\s+(my|his|her|our|their|the)\s+(?!day\b|night\b|time\b|week\b|weekend\b)\w+|"
    r"cost|costs|expense|expenses|tax\s+return|inheritance|"
    # --- Physical / household labour (specific forms to avoid false positives) ---
    # 'work' alone is too broad ('at work', 'boss at work') — require compound forms
    r"housework|housekeeping|overtime|unpaid\s+work|extra\s+work|"
    r"shift(?:s)?\b|chores?|laundry|"
    # 'cleaning' (not 'clean' alone — avoids 'been clean' = sobriety)
    r"cleaning|cooking|doing\s+the\s+dishes|"
    # --- Care labour (specific constructions) ---
    r"care\s+for|caring\s+for|look\s+after|looking\s+after|"
    r"childcare|child\s+care|babysit|babysitting|caregiving|caregiver|"
    r"taking\s+care\s+of|takes?\s+care\s+of|"
    # --- Resource / cost sharing ---
    r"split(?:ting)?|fair\s+share|equal\s+share"
    r")\b",
    re.IGNORECASE,
)


def _is_justice_relevant(action_desc: str, title: str, text: str = "") -> bool:
    """Return True if the record likely involves a justice-relevant cost structure.

    Matches only against the action description and title (not the full post
    body) to prevent false positives from incidental keyword occurrences.
    The ``text`` parameter is accepted for API compatibility but ignored.
    """
    return bool(_JUSTICE_RE.search(f"{action_desc} {title}"))


# ---------------------------------------------------------------------------
# Role extraction
# ---------------------------------------------------------------------------

_ROLE_RE = re.compile(
    r"\bmy\b[\s\w]{0,8}?"
    r"(wife|husband|partner|boyfriend|girlfriend|"
    r"mother|father|mom|dad|parent|child|son|daughter|sibling|sister|brother|"
    r"boss|manager|employer|employee|coworker|colleague|subordinate|"
    r"landlord|tenant|friend|neighbour|neighbor|roommate|flatmate)\b",
    re.IGNORECASE,
)


def _extract_target_role(action_desc: str, title: str) -> str:
    """Heuristically extract the target role from the action description or title."""
    for text in (action_desc, title):
        m = _ROLE_RE.search(text)
        if m:
            return m.group(1).lower()
    return "other person"


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------


def load_anecdotes(
    path: str | Path,
    min_votes: int = 3,
    max_votes_per_side: int = 50,
    max_records: Optional[int] = None,
) -> Tuple[List[Scenario], List[SurveyResponse]]:
    """Load SCRUPLES Anecdotes and return (scenarios, survey_responses).

    Each record with a non-null ``action`` becomes one ``Scenario``.
    Binarized vote counts are expanded into individual ``SurveyResponse``
    objects with responses ``"Right"`` or ``"Wrong"``.

    Parameters
    ----------
    path:
        Path to a ``.scruples-anecdotes.jsonl`` file.
    min_votes:
        Drop records whose total (capped) vote count is below this threshold.
        Default 3.
    max_votes_per_side:
        Cap the number of Right / Wrong responses per scenario to prevent
        high-vote posts from dominating. Default 50.
    max_records:
        If given, sub-sample up to this many records before processing.

    Returns
    -------
    scenarios:
        One ``Scenario`` per record that passes filters.
    survey_responses:
        One ``SurveyResponse`` per (capped) vote.
    """
    path = Path(path)
    records = []
    with open(path) as fh:
        for line in fh:
            records.append(json.loads(line))

    if max_records is not None:
        records = records[:max_records]

    action_descs = [r["action"]["description"] for r in records if r["action"]]
    action_idx = {d: i for i, d in enumerate(dict.fromkeys(action_descs))}

    scenarios: List[Scenario] = []
    survey_responses: List[SurveyResponse] = []

    for rec in records:
        if not rec["action"]:
            continue

        scores = rec["binarized_label_scores"]
        n_right = min(scores.get("RIGHT", 0), max_votes_per_side)
        n_wrong = min(scores.get("WRONG", 0), max_votes_per_side)

        if n_right + n_wrong < min_votes:
            continue

        action_desc = rec["action"]["description"]
        post_id = rec["post_id"]
        a_idx = action_idx[action_desc]
        scenario_id = f"sc_{a_idx}_{post_id}"

        scenario = Scenario(
            id=scenario_id,
            representation=rec["title"],
            anchors={"action": action_desc},
            origin={
                "source": "scruples_anecdotes",
                "post_id": post_id,
                "post_type": rec.get("post_type", ""),
            },
        )
        scenarios.append(scenario)

        for i in range(n_right):
            survey_responses.append(
                SurveyResponse(
                    participant_id=f"sc_vote_{post_id}_right_{i}",
                    scenario_id=scenario_id,
                    response="Right",
                )
            )
        for i in range(n_wrong):
            survey_responses.append(
                SurveyResponse(
                    participant_id=f"sc_vote_{post_id}_wrong_{i}",
                    scenario_id=scenario_id,
                    response="Wrong",
                )
            )

    return scenarios, survey_responses


def load_justice_subset(
    path: str | Path,
    min_votes: int = 5,
    max_votes_per_side: int = 50,
    max_records: Optional[int] = None,
) -> Tuple[List[Scenario], List[SurveyResponse]]:
    """Load a justice-filtered subset of SCRUPLES Anecdotes with role annotations.

    Applies keyword heuristics to select interpersonal scenarios where a clear
    agent-target dynamic exists. Suitable for justice and effort dimension
    surveys with role support.

    Each ``SurveyResponse`` has ``role_perspective="observer"`` because the
    Reddit community acts as a third-party observer when voting.

    Judgment map: ``JUSTICE_JUDGMENT_MAP = {"Just": 1, "Neutral": 0, "Unjust": -1}``

    Parameters
    ----------
    path:
        Path to a ``.scruples-anecdotes.jsonl`` file.
    min_votes:
        Minimum total (capped) votes required. Default 5.
    max_votes_per_side:
        Cap per-side vote counts. Default 50.
    max_records:
        If given, sub-sample up to this many justice-relevant records before
        expanding votes.

    Returns
    -------
    scenarios:
        One ``Scenario`` per filtered record, with ``roles`` populated.
        ID format: ``scj_{action_idx}_{post_id}``
    survey_responses:
        One ``SurveyResponse`` (``"Just"`` or ``"Unjust"``) per (capped) vote,
        with ``role_perspective="observer"``.
    """
    path = Path(path)
    records = []
    with open(path) as fh:
        for line in fh:
            records.append(json.loads(line))

    records = [
        r
        for r in records
        if r["action"]
        and _is_justice_relevant(
            r["action"]["description"],
            r.get("title", ""),
            r.get("text", ""),
        )
    ]

    if max_records is not None:
        records = records[:max_records]

    action_descs = [r["action"]["description"] for r in records]
    action_idx = {d: i for i, d in enumerate(dict.fromkeys(action_descs))}

    scenarios: List[Scenario] = []
    survey_responses: List[SurveyResponse] = []

    for rec in records:
        scores = rec["binarized_label_scores"]
        n_just = min(scores.get("RIGHT", 0), max_votes_per_side)
        n_unjust = min(scores.get("WRONG", 0), max_votes_per_side)

        if n_just + n_unjust < min_votes:
            continue

        action_desc = rec["action"]["description"]
        post_id = rec["post_id"]
        a_idx = action_idx[action_desc]
        scenario_id = f"scj_{a_idx}_{post_id}"

        target_role = _extract_target_role(action_desc, rec.get("title", ""))

        scenario = Scenario(
            id=scenario_id,
            representation=rec["title"],
            anchors={"action": action_desc},
            roles={"agent": "author", "target": target_role},
            origin={"source": "scruples_justice", "post_id": post_id},
        )
        scenarios.append(scenario)

        for i in range(n_just):
            survey_responses.append(
                SurveyResponse(
                    participant_id=f"scj_vote_{post_id}_just_{i}",
                    scenario_id=scenario_id,
                    response="Just",
                    role_perspective="observer",
                )
            )
        for i in range(n_unjust):
            survey_responses.append(
                SurveyResponse(
                    participant_id=f"scj_vote_{post_id}_unjust_{i}",
                    scenario_id=scenario_id,
                    response="Unjust",
                    role_perspective="observer",
                )
            )

    return scenarios, survey_responses


# ---------------------------------------------------------------------------
# Survey scenario selection
# ---------------------------------------------------------------------------

_AITA_RE = re.compile(r"^AITA\s+(for\s+)?", re.IGNORECASE)
_WIBTA_RE = re.compile(r"^WIBTA", re.IGNORECASE)

# Slurs and offensive terms that disqualify a scenario from public surveys
_SLUR_RE = re.compile(
    r"\b(faggot|nigger|nigga|retard|bitch|cunt|fuck|shit)\b|n-word",
    re.IGNORECASE,
)

# Typo pattern: consecutive consonants unlikely in English (crude typo detector)
_OBVIOUS_TYPO_RE = re.compile(r"\boay\b|\basy\b|\bteh\b", re.IGNORECASE)


def _clean_title(title: str) -> str:
    """Strip 'AITA for ' prefix, remove trailing '?', and capitalise."""
    t = _AITA_RE.sub("", title).rstrip("?").strip()
    # Strip residual leading "For " (capitalised or lowercase) left after prefix removal
    t = re.sub(r"^[Ff]or\s+", "", t).strip()
    return t[0].upper() + t[1:] if t else t


def select_survey_scenarios(
    path: str | Path,
    n_unjust: int = 15,
    n_ambiguous: int = 10,
    n_just: int = 15,
    min_votes: int = 10,
    max_title_len: int = 100,
    seed: int = 42,
) -> list:
    """Select a balanced set of SCRUPLES justice scenarios suitable for a survey.

    Filters the justice subset and picks scenarios balanced across three moral
    valence bands: clearly unjust, ambiguous, and clearly just (based on the
    community vote margin).  Within each band, role diversity is maximised.

    Parameters
    ----------
    path:
        Path to a ``.scruples-anecdotes.jsonl`` file.
    n_unjust, n_ambiguous, n_just:
        Number of scenarios to draw from each valence band.
    min_votes:
        Minimum total votes required. Default 10.
    max_title_len:
        Maximum cleaned-title length. Longer titles are dropped. Default 100.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    list of dicts, each with keys:
        ``id``, ``text``, ``action``, ``agent_role``, ``target_role``,
        ``total_votes``, ``pct_wrong``
    """
    import random as _random

    path = Path(path)
    records = []
    with open(path) as fh:
        for line in fh:
            records.append(json.loads(line))

    records = [
        r for r in records
        if r["action"]
        and _is_justice_relevant(r["action"]["description"], r.get("title", ""), r.get("text", ""))
    ]

    candidates = []
    for r in records:
        desc = r["action"]["description"]
        title = r.get("title", "")
        target = _extract_target_role(desc, title)
        if target == "other person":
            continue
        n_right = r["binarized_label_scores"]["RIGHT"]
        n_wrong = r["binarized_label_scores"]["WRONG"]
        total = n_right + n_wrong
        if total < min_votes:
            continue
        text = _clean_title(title)
        if not text or len(text) > max_title_len or len(text) < 20:
            continue
        # Drop WIBTA titles (conditional phrasing doesn't clean up well)
        if _WIBTA_RE.match(title):
            continue
        # Drop scenarios containing slurs, offensive language, or obvious typos
        if _SLUR_RE.search(text) or _SLUR_RE.search(desc):
            continue
        if _OBVIOUS_TYPO_RE.search(text) or _OBVIOUS_TYPO_RE.search(desc):
            continue
        candidates.append({
            "id": f"scj_{r['post_id']}",
            "text": text,
            "action": desc,
            "agent_role": "author",
            "target_role": target,
            "total_votes": total,
            "pct_wrong": round(n_wrong / total, 3),
        })

    def _pick_diverse(pool: list, n: int) -> list:
        pool = sorted(pool, key=lambda x: -x["total_votes"])
        seen: set = set()
        first_pass: list = []
        for c in pool:
            if c["target_role"] not in seen or len(first_pass) < n // 2:
                first_pass.append(c)
                seen.add(c["target_role"])
        for c in pool:
            if c not in first_pass:
                first_pass.append(c)
        return first_pass[:n]

    _random.seed(seed)
    unjust    = [c for c in candidates if c["pct_wrong"] > 0.70]
    ambiguous = [c for c in candidates if 0.35 <= c["pct_wrong"] <= 0.65]
    just      = [c for c in candidates if c["pct_wrong"] < 0.25]

    return (
        _pick_diverse(unjust, n_unjust)
        + _pick_diverse(ambiguous, n_ambiguous)
        + _pick_diverse(just, n_just)
    )
