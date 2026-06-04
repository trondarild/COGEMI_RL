# tests/test_role_arm_surveys.py
"""
Structural tests for the three role-arm v2 survey HTML files:
  appropriateness_survey_aspects_park_prolific_v2_{agent,target,observer}.html

Tests verify:
  - Each file contains the correct ROLE constant
  - Q1 and Q2 question text is role-specific and present
  - Consent intro includes role-framing sentence
  - Title includes role label
  - ROLE field is saved in the Supabase base row (submitScenario)
  - Completion code placeholder is arm-specific
  - Scenario pool, attention checks, and retest IDs are identical across arms
  - v2 base is unchanged in non-role sections (Supabase URL, scale labels)
"""
import re
import pathlib
import pytest

SURVEY_DIR = pathlib.Path("cogemi/survey")
V2_BASE    = SURVEY_DIR / "appropriateness_survey_aspects_park_prolific_v2.html"

ARMS = ["agent", "target", "observer"]

def _html(role: str) -> str:
    path = SURVEY_DIR / f"appropriateness_survey_aspects_park_prolific_v2_{role}.html"
    return path.read_text(encoding="utf-8")

def _base_html() -> str:
    return V2_BASE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ARMS)
def test_file_exists(role):
    path = SURVEY_DIR / f"appropriateness_survey_aspects_park_prolific_v2_{role}.html"
    assert path.exists(), f"Missing file: {path}"


# ---------------------------------------------------------------------------
# ROLE constant
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ARMS)
def test_role_constant_present(role):
    html = _html(role)
    assert f'var ROLE = "{role}";' in html, \
        f"ROLE constant not set to '{role}'"


def test_role_constants_are_distinct():
    roles = {role: _html(role).count(f'var ROLE = "{role}";') for role in ARMS}
    for role, count in roles.items():
        assert count == 1, f"Expected exactly 1 ROLE declaration in {role} arm, got {count}"


# ---------------------------------------------------------------------------
# ROLE stored in Supabase base row
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ARMS)
def test_role_in_supabase_base_row(role):
    html = _html(role)
    assert "role:        ROLE" in html, \
        f"'role: ROLE' not found in submitScenario base object for {role} arm"


# ---------------------------------------------------------------------------
# Q1 question text — role-specific framing
# ---------------------------------------------------------------------------

EXPECTED_Q1 = {
    "agent":    "Imagining yourself as the person performing this action",
    "target":   "Imagining yourself as the person this action is directed at",
    "observer": "Imagining yourself as an outside observer",
}

@pytest.mark.parametrize("role", ARMS)
def test_q1_question_role_framing(role):
    html = _html(role)
    assert EXPECTED_Q1[role] in html, \
        f"Q1 role framing not found for {role}: expected '{EXPECTED_Q1[role]}'"


def test_q1_framing_unique_per_arm():
    """Each arm's Q1 framing must not appear in the other arms."""
    htmls = {role: _html(role) for role in ARMS}
    for role, fragment in EXPECTED_Q1.items():
        for other in ARMS:
            if other != role:
                assert fragment not in htmls[other], \
                    f"Q1 framing for '{role}' found in '{other}' arm — arms are not distinct"


# ---------------------------------------------------------------------------
# Q2 question text — role-specific
# ---------------------------------------------------------------------------

EXPECTED_Q2_FRAGMENTS = {
    "agent":    "in the same position (performing this action)",
    "target":   "on the receiving end",
    "observer": "observing this situation",
}

@pytest.mark.parametrize("role", ARMS)
def test_q2_question_role_framing(role):
    html = _html(role)
    assert EXPECTED_Q2_FRAGMENTS[role] in html, \
        f"Q2 role framing not found for {role}: expected '{EXPECTED_Q2_FRAGMENTS[role]}'"


# ---------------------------------------------------------------------------
# Consent intro — role framing sentence
# ---------------------------------------------------------------------------

EXPECTED_CONSENT = {
    "agent":    "the person performing the action",
    "target":   "the person on the receiving end of the action",
    "observer": "an outside observer watching the scene",
}

@pytest.mark.parametrize("role", ARMS)
def test_consent_role_framing(role):
    html = _html(role)
    assert EXPECTED_CONSENT[role] in html, \
        f"Consent role framing not found for {role}"


# ---------------------------------------------------------------------------
# Title and perspective label
# ---------------------------------------------------------------------------

EXPECTED_TITLES = {
    "agent":    "Agent Perspective",
    "target":   "Target Perspective",
    "observer": "Observer Perspective",
}

@pytest.mark.parametrize("role", ARMS)
def test_title_contains_role_label(role):
    html = _html(role)
    assert EXPECTED_TITLES[role] in html, \
        f"Title/label for {role} arm not found"


# ---------------------------------------------------------------------------
# Arm-specific completion code placeholders
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ARMS)
def test_completion_code_placeholder(role):
    html  = _html(role)
    token = f"{role.upper()}_CC_PLACEHOLDER"
    assert token in html, \
        f"Completion code placeholder '{token}' not found in {role} arm"


def test_completion_codes_are_distinct():
    """No arm should carry another arm's completion code placeholder."""
    for role in ARMS:
        html  = _html(role)
        token = f"{role.upper()}_CC_PLACEHOLDER"
        for other in ARMS:
            if other != role:
                wrong = f"{other.upper()}_CC_PLACEHOLDER"
                assert wrong not in html, \
                    f"'{wrong}' found in {role} arm — completion codes are mixed up"


# ---------------------------------------------------------------------------
# Scenario pool integrity — identical across all arms and matching v2
# ---------------------------------------------------------------------------

def _extract_scenario_ids(html: str):
    return re.findall(r'\{ id:"([^"]+)"', html)


def test_scenario_pool_identical_across_arms():
    ids = {role: _extract_scenario_ids(_html(role)) for role in ARMS}
    reference = ids[ARMS[0]]
    for role in ARMS[1:]:
        assert ids[role] == reference, \
            f"Scenario pool differs between '{ARMS[0]}' and '{role}' arms"


def test_scenario_pool_matches_v2_base():
    base_ids = _extract_scenario_ids(_base_html())
    for role in ARMS:
        arm_ids = _extract_scenario_ids(_html(role))
        assert arm_ids == base_ids, \
            f"Scenario pool in {role} arm differs from v2 base"


def test_scenario_pool_size():
    """40 main + 2 attention checks declared; RETEST_IDS adds 5 at runtime."""
    for role in ARMS:
        ids = _extract_scenario_ids(_html(role))
        # 40 pool + 2 attention checks
        assert len(ids) == 42, \
            f"Expected 42 declared scenarios in {role} arm, got {len(ids)}"


# ---------------------------------------------------------------------------
# Supabase config unchanged from v2
# ---------------------------------------------------------------------------

def test_supabase_url_unchanged():
    base_url = re.search(r'var SUPABASE_URL\s*=\s*"([^"]+)"', _base_html()).group(1)
    for role in ARMS:
        arm_url = re.search(r'var SUPABASE_URL\s*=\s*"([^"]+)"', _html(role)).group(1)
        assert arm_url == base_url, \
            f"Supabase URL changed in {role} arm"


def test_supabase_table_is_responses_v2():
    for role in ARMS:
        assert "/rest/v1/responses_v2" in _html(role), \
            f"Supabase table not responses_v2 in {role} arm"


# ---------------------------------------------------------------------------
# Scale labels unchanged
# ---------------------------------------------------------------------------

def test_likert_labels_unchanged():
    expected = '"Strongly\\ninappropriate", "Inappropriate", "Neutral", "Appropriate", "Strongly\\nappropriate"'
    for role in ARMS:
        assert expected in _html(role), \
            f"Likert scale labels changed in {role} arm"


def test_q3_empirical_labels_unchanged():
    for role in ARMS:
        assert '"Rarely", "Sometimes", "Often"' in _html(role), \
            f"Q3 empirical labels changed in {role} arm"
